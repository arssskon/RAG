"""Загрузка и парсинг PDF файлов."""

import io
import re
from typing import Generator
from pypdf import PdfReader


class PDFLoader:
    """Класс для загрузки PDF и извлечения текста постранично."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def extract_pages(
        self,
        file_content: bytes,
        filename: str
    ) -> Generator[tuple[int, str], None, None]:
        """Извлекает текст из PDF постранично."""
        self.errors = []
        self.warnings = []

        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            total_pages = len(pdf_reader.pages)

            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    page_number = page_num + 1

                    if text and text.strip():
                        cleaned_text = self._clean_text(text)
                        yield page_number, cleaned_text
                    else:
                        self.warnings.append(
                            f"Страница {page_number} в '{filename}' пустая"
                        )
                except Exception as e:
                    self.errors.append(
                        f"Ошибка страницы {page_num + 1}: {str(e)}"
                    )
        except Exception as e:
            self.errors.append(f"Ошибка открытия PDF '{filename}': {str(e)}")

    def _clean_text(self, text: str) -> str:
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def load_pdf(self, file_content: bytes, filename: str) -> list[tuple[int, str]]:
        return list(self.extract_pages(file_content, filename))

    def get_errors(self) -> list[str]:
        return self.errors

    def get_warnings(self) -> list[str]:
        return self.warnings


def validate_pdf(file_content: bytes) -> tuple[bool, str]:
    """Проверяет валидность PDF."""
    try:
        if not file_content.startswith(b'%PDF'):
            return False, "Файл не является PDF документом"
        pdf_reader = PdfReader(io.BytesIO(file_content))
        if len(pdf_reader.pages) == 0:
            return False, "PDF файл не содержит страниц"
        return True, ""
    except Exception as e:
        return False, f"Ошибка при валидации PDF: {str(e)}"
