"""Поиск релевантных документов."""

from .vectorstore import VectorStoreManager
from .schemas import SearchResult


class Retriever:
    def __init__(self, vectorstore: VectorStoreManager):
        self.vectorstore = vectorstore

    def retrieve(self, query: str, top_k: int = 5) -> list[SearchResult]:
        top_k = max(3, min(10, top_k))
        return self.vectorstore.search(query, top_k=top_k)

    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5
    ) -> tuple[list[SearchResult], str]:
        results = self.retrieve(query, top_k)
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Фрагмент {i}] Источник: {result.source}, стр. {result.page}\n"
                f"{result.text}"
            )
        context = "\n\n---\n\n".join(context_parts)
        return results, context

    def has_index(self) -> bool:
        return self.vectorstore.collection_exists()
