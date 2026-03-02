"""Обёртка для работы с LLM и генерации ответов."""

import os
import re
from .schemas import RAGResponse, SearchResult, SourceReference, Citation

SYSTEM_PROMPT = """Ты — ассистент для ответов на вопросы по учебным конспектам.

ПРАВИЛА:
1. Отвечай ТОЛЬКО на основе предоставленного контекста.
2. Если в контексте нет информации — честно скажи об этом.
3. Давай краткие ответы (5-10 предложений).
4. Указывай источники (файл и страницы).
5. Приводи 2-4 цитаты из контекста.

ФОРМАТ ОТВЕТА:
Ответ, затем:
- "Источники:" — файлы и страницы
- "Цитаты:" — 2-4 релевантные цитаты

Отвечай на русском языке."""


class LLMWrapper:
    def __init__(self):
        self._client = None
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._has_api_key = bool(os.getenv("OPENAI_API_KEY"))

    @property
    def has_llm(self) -> bool:
        return self._has_api_key

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def generate_response(
        self,
        query: str,
        context: str,
        search_results: list[SearchResult]
    ) -> RAGResponse:
        if not self.has_llm:
            return self._create_search_only_response(search_results)
        try:
            client = self._get_client()
            user_prompt = f"""Вопрос: {query}

Контекст из конспектов:
{context}

Ответь на вопрос, используя только информацию из контекста."""

            response = client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            answer_text = response.choices[0].message.content
            return self._parse_llm_response(answer_text, search_results)
        except Exception as e:
            return RAGResponse(
                answer=f"Ошибка LLM: {str(e)}",
                context_used=search_results,
                is_search_only=True
            )

    def _parse_llm_response(
        self,
        answer_text: str,
        search_results: list[SearchResult]
    ) -> RAGResponse:
        sources_dict: dict[str, list[int]] = {}
        for result in search_results[:3]:
            if result.source not in sources_dict:
                sources_dict[result.source] = []
            if result.page not in sources_dict[result.source]:
                sources_dict[result.source].append(result.page)
        sources = [
            SourceReference(source=src, pages=pages)
            for src, pages in sources_dict.items()
        ]
        citations = []
        for result in search_results[:4]:
            sentences = re.split(r'(?<=[.!?])\s+', result.text)
            if sentences:
                citation_text = sentences[0][:150]
                if len(sentences[0]) > 150:
                    citation_text += "..."
                citations.append(Citation(
                    text=citation_text,
                    source=result.source,
                    page=result.page
                ))
        return RAGResponse(
            answer=answer_text,
            sources=sources,
            citations=citations[:4],
            context_used=search_results,
            is_search_only=False
        )

    def _create_search_only_response(
        self,
        search_results: list[SearchResult]
    ) -> RAGResponse:
        return RAGResponse(
            answer="Режим без LLM: доступен только поиск по конспектам.",
            context_used=search_results,
            is_search_only=True
        )


def check_openai_connection() -> tuple[bool, str]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, "OPENAI_API_KEY не установлен"
    try:
        from openai import OpenAI
        client = OpenAI()
        client.models.list()
        return True, "Подключение к OpenAI успешно"
    except Exception as e:
        return False, f"Ошибка: {str(e)}"
