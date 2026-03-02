"""Управление векторным хранилищем ChromaDB."""

import os
import shutil
from datetime import datetime
from typing import Optional, Any

import chromadb
from chromadb.config import Settings
from chromadb import CloudClient

from .schemas import Chunk, IndexStats, SearchResult

CHROMA_PERSIST_DIR = "./chroma_store"
DEFAULT_COLLECTION = "course_notes"


class EmbeddingFunction:
    def __call__(self, input: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OpenAIEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model: str = "text-embedding-3-small"):
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model

    def __call__(self, input: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=input)
        return [item.embedding for item in response.data]


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(input)
        return embeddings.tolist()


def get_embedding_function() -> tuple[EmbeddingFunction, bool]:
    openai_key = os.getenv("OPENAI_API_KEY")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    if openai_key:
        try:
            return OpenAIEmbeddingFunction(model=embedding_model), True
        except Exception as e:
            print(f"Ошибка OpenAI embeddings: {e}")
    return SentenceTransformerEmbeddingFunction(), False


class VectorStoreManager:
    def __init__(
        self,
        persist_dir: str = CHROMA_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION
    ):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self._client: Optional[Any] = None
        self._collection = None
        self._embedding_fn, self._has_openai = get_embedding_function()
        self._stats_file = os.path.join(persist_dir, "stats.txt")

    @property
    def has_openai(self) -> bool:
        return self._has_openai

    def _get_client(self):
        if self._client is None:
            chroma_api_key = os.getenv("CHROMA_API_KEY")
            chroma_tenant = os.getenv("CHROMA_TENANT")
            chroma_database = os.getenv("CHROMA_DATABASE")

            if chroma_api_key and chroma_tenant and chroma_database:
                # Облачный ChromaDB
                self._client = CloudClient(
                    api_key=chroma_api_key,
                    tenant=chroma_tenant,
                    database=chroma_database,
                )
            else:
                # Локальный ChromaDB
                os.makedirs(self.persist_dir, exist_ok=True)
                self._client = chromadb.PersistentClient(
                    path=self.persist_dir,
                    settings=Settings(anonymized_telemetry=False)
                )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_chunks(self, chunks: list[Chunk], batch_size: int = 100) -> int:
        collection = self._get_collection()
        total_added = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.text for c in batch]
            ids = [c.metadata.chunk_id for c in batch]
            metadatas = [c.metadata.to_dict() for c in batch]
            embeddings = self._embedding_fn(texts)
            collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            total_added += len(batch)
        self._save_last_indexed()
        return total_added

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        collection = self._get_collection()
        if collection.count() == 0:
            return []
        query_embedding = self._embedding_fn([query])[0]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        search_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if results["distances"] else None
                score = 1 - distance if distance is not None else None
                search_results.append(SearchResult(
                    text=doc,
                    source=metadata.get("source", "unknown"),
                    page=metadata.get("page", 0),
                    score=score,
                    chunk_id=metadata.get("chunk_id", "")
                ))
        return search_results

    def get_stats(self) -> IndexStats:
        try:
            collection = self._get_collection()
            count = collection.count()
            sources = set()
            if count > 0:
                all_data = collection.get(include=["metadatas"])
                if all_data["metadatas"]:
                    for meta in all_data["metadatas"]:
                        if meta and "source" in meta:
                            sources.add(meta["source"])
            last_indexed = self._read_last_indexed()
            return IndexStats(
                num_documents=len(sources),
                num_chunks=count,
                last_indexed=last_indexed,
                sources=list(sources)
            )
        except Exception as e:
            print(f"Ошибка статистики: {e}")
            return IndexStats()

    def reset_index(self) -> bool:
        try:
            # Сброс коллекции в облачном/локальном Chroma
            if self._collection is not None:
                try:
                    client = self._get_client()
                    client.delete_collection(self.collection_name)
                except Exception:
                    # Если коллекция не существует или клиент не поддерживает удаление — игнорируем
                    pass

            self._collection = None
            self._client = None
            if os.path.exists(self.persist_dir):
                shutil.rmtree(self.persist_dir)
            return True
        except Exception as e:
            print(f"Ошибка сброса: {e}")
            return False

    def _save_last_indexed(self):
        os.makedirs(self.persist_dir, exist_ok=True)
        with open(self._stats_file, "w") as f:
            f.write(datetime.now().isoformat())

    def _read_last_indexed(self) -> Optional[datetime]:
        try:
            if os.path.exists(self._stats_file):
                with open(self._stats_file, "r") as f:
                    return datetime.fromisoformat(f.read().strip())
        except Exception:
            pass
        return None

    def collection_exists(self) -> bool:
        try:
            stats = self.get_stats()
            return stats.num_chunks > 0
        except Exception:
            return False
