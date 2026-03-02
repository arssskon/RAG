"""Разбиение текста на чанки с перекрытием."""

import re
from typing import Generator
from .schemas import ChunkMetadata, Chunk


class TextChunker:
    """Класс для разбиения текста на чанки."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text(self, text: str) -> list[str]:
        chunks = []
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []

        sentences = self._split_into_sentences(text)
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                if chunks and self.chunk_overlap > 0:
                    overlap_text = self._get_overlap(chunks[-1])
                    current_chunk = overlap_text + sentence
                else:
                    current_chunk = sentence
                if len(current_chunk) > self.chunk_size * 1.5:
                    sub_chunks = self._split_long_text(current_chunk)
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""

        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        return chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        result = []
        for i, s in enumerate(sentences):
            if i < len(sentences) - 1:
                result.append(s + " ")
            else:
                result.append(s)
        return result

    def _get_overlap(self, text: str) -> str:
        if len(text) <= self.chunk_overlap:
            return text + " "
        overlap_zone = text[-self.chunk_overlap:]
        match = re.search(r'[.!?]\s+', overlap_zone)
        if match:
            return overlap_zone[match.end():]
        return overlap_zone

    def _split_long_text(self, text: str) -> list[str]:
        chunks = []
        while len(text) > self.chunk_size:
            split_point = self.chunk_size
            space_pos = text.rfind(' ', 0, self.chunk_size)
            if space_pos > self.chunk_size // 2:
                split_point = space_pos
            chunks.append(text[:split_point].strip())
            overlap_start = max(0, split_point - self.chunk_overlap)
            text = text[overlap_start:]
        if text.strip():
            chunks.append(text.strip())
        return chunks

    def chunk_pages(
        self,
        pages: list[tuple[int, str]],
        source: str
    ) -> Generator[Chunk, None, None]:
        chunk_counter = 0
        for page_num, page_text in pages:
            if not page_text.strip():
                continue
            chunks = self._split_text(page_text)
            for chunk_text in chunks:
                chunk_id = f"{source}_p{page_num}_c{chunk_counter}"
                metadata = ChunkMetadata(
                    source=source,
                    page=page_num,
                    chunk_id=chunk_id,
                )
                yield Chunk(text=chunk_text, metadata=metadata)
                chunk_counter += 1

    def chunk_document(
        self,
        pages: list[tuple[int, str]],
        source: str
    ) -> list[Chunk]:
        return list(self.chunk_pages(pages, source))
