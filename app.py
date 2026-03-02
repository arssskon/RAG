"""RAG Chat по PDF-конспектам курса."""

import streamlit as st
from datetime import datetime
import os

from dotenv import load_dotenv
load_dotenv()

from rag.vectorstore import VectorStoreManager

st.set_page_config(
    page_title="RAG Chat | PDF Конспекты",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "logs" not in st.session_state:
    st.session_state.logs = []

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = VectorStoreManager()


def add_log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    st.session_state.logs.append(log_entry)
    if len(st.session_state.logs) > 20:
        st.session_state.logs = st.session_state.logs[-20:]
    print(log_entry)


def render_sidebar():
    with st.sidebar:
        st.title("📚 RAG Chat")
        st.markdown("---")

        st.subheader("Статус индекса")
        try:
            stats = st.session_state.vectorstore.get_stats()
            if stats.is_empty():
                st.warning("Индекс пуст")
                st.caption("Загрузите PDF на странице 'Индексация'")
            else:
                st.success("Индекс готов")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Документов", stats.num_documents)
                with col2:
                    st.metric("Чанков", stats.num_chunks)
                if stats.last_indexed:
                    st.caption(f"Обновлен: {stats.last_indexed.strftime('%d.%m.%Y %H:%M')}")
                if stats.sources:
                    with st.expander("Источники"):
                        for src in stats.sources:
                            st.text(f"• {src}")
        except Exception as e:
            st.error(f"Ошибка: {e}")

        st.markdown("---")
        st.subheader("Настройки поиска")
        top_k = st.slider("Количество результатов (top_k)", min_value=3, max_value=10, value=5)
        st.session_state.top_k = top_k

        index_mode = st.radio(
            "Режим индексации",
            ["add", "rebuild"],
            format_func=lambda x: "Добавить" if x == "add" else "Пересоздать"
        )
        st.session_state.index_mode = index_mode

        st.markdown("---")
        st.subheader("Режим работы")
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        if has_openai:
            st.success("OpenAI API доступен")
            st.caption(f"Модель: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini')}")
        else:
            st.warning("Режим только поиска")
            st.caption("Установите OPENAI_API_KEY для генерации ответов")

        st.markdown("---")
        with st.expander("Логи"):
            if st.session_state.logs:
                for log in reversed(st.session_state.logs[-10:]):
                    st.text(log)
            else:
                st.caption("Логи пусты")


render_sidebar()

st.title("📚 RAG Chat по PDF-конспектам")

st.markdown("""
Добро пожаловать в RAG Chat — приложение для умного поиска и ответов
на вопросы по вашим учебным материалам.

### Как использовать:

1. **Индексация** — загрузите PDF-файлы с конспектами/лекциями
2. **Чат** — задавайте вопросы и получайте ответы на основе загруженных материалов
3. **О приложении** — узнайте больше о том, как работает RAG

---

### Быстрый старт

Перейдите на страницу **"Индексация"** в меню слева, чтобы загрузить первые PDF-файлы.
""")

stats = st.session_state.vectorstore.get_stats()

col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"**Документов в индексе:** {stats.num_documents}")
with col2:
    st.info(f"**Чанков в индексе:** {stats.num_chunks}")
with col3:
    if stats.last_indexed:
        st.info(f"**Последнее обновление:** {stats.last_indexed.strftime('%d.%m.%Y')}")
    else:
        st.info("**Последнее обновление:** —")

if stats.is_empty():
    st.warning("👆 Начните с загрузки PDF-файлов на странице 'Индексация'")
else:
    st.success("✅ Индекс готов! Перейдите в 'Чат' для поиска по материалам.")
