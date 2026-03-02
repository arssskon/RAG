"""Схемы данных для RAG пайплайна."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ChunkMetadata:
    """Метаданные чанка текста."""
    source: str
    page: int
    chunk_id: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "page": self.page,
            "chunk_id": self.chunk_id,
        }


@dataclass
class Chunk:
    """Чанк текста с метаданными."""
    text: str
    metadata: ChunkMetadata

    def to_document(self) -> dict:
        return {
            "content": self.text,
            "metadata": self.metadata.to_dict(),
        }


@dataclass
class SearchResult:
    """Результат поиска."""
    text: str
    source: str
    page: int
    score: Optional[float] = None
    chunk_id: str = ""

    @property
    def header(self) -> str:
        score_str = f" (score: {self.score:.3f})" if self.score is not None else ""
        return f"[{self.source}] стр. {self.page}{score_str}"


@dataclass
class SourceReference:
    """Ссылка на источник."""
    source: str
    pages: list[int] = field(default_factory=list)

    def __str__(self) -> str:
        pages_str = ", ".join(map(str, sorted(set(self.pages))))
        return f"{self.source} (стр. {pages_str})"


@dataclass
class Citation:
    """Цитата из контекста."""
    text: str
    source: str
    page: int

    def __str__(self) -> str:
        return f'"{self.text}" — {self.source}, стр. {self.page}'


@dataclass
class RAGResponse:
    """Ответ RAG системы."""
    answer: str
    sources: list[SourceReference] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    context_used: list[SearchResult] = field(default_factory=list)
    is_search_only: bool = False


@dataclass
class IndexStats:
    """Статистика индекса."""
    num_documents: int = 0
    num_chunks: int = 0
    last_indexed: Optional[datetime] = None
    sources: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return self.num_chunks == 0


@dataclass
class LogEntry:
    """Запись лога."""
    timestamp: datetime
    level: str
    message: str

    def __str__(self) -> str:
        return f"[{self.timestamp.strftime('%H:%M:%S')}] {self.level}: {self.message}"
