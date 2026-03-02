"""Страница чата для вопросов и ответов."""

import streamlit as st
from datetime import datetime

from rag.vectorstore import VectorStoreManager
from rag.retriever import Retriever
from rag.llm import LLMWrapper

st.set_page_config(page_title="Чат | RAG Chat", page_icon="💬", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }

    .page-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2EC4B6 0%, #CBF3F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .page-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 1.5rem; }

    .chat-input-container {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
    }

    .result-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border-left: 4px solid #FF6B35;
    }

    .result-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }

    .result-source {
        font-weight: 700;
        color: #1A1A2E;
    }

    .result-score {
        background: linear-gradient(135deg, #2EC4B6 0%, #CBF3F0 100%);
        color: #1A1A2E;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .result-text {
        color: #444;
        line-height: 1.7;
    }

    .answer-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border-radius: 20px;
        padding: 2rem;
        color: white;
        margin: 1.5rem 0;
    }

    .answer-title {
        color: #FF6B35;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    .answer-text {
        line-height: 1.8;
        font-size: 1.05rem;
    }

    .sources-section {
        background: rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-top: 1.5rem;
    }

    .sources-title {
        color: #2EC4B6;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .citation-item {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
        font-style: italic;
        border-left: 3px solid #FF6B35;
    }

    .citation-source {
        font-style: normal;
        font-size: 0.85rem;
        color: #F7C59F;
        margin-top: 0.25rem;
    }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: white; }

    .stButton > button { border-radius: 12px; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(46,196,182,0.3); }

    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e9ecef;
        font-size: 1.05rem;
    }

    .stTextArea textarea:focus {
        border-color: #2EC4B6;
        box-shadow: 0 0 0 3px rgba(46,196,182,0.2);
    }

    .stAlert { border-radius: 12px; }

    .mode-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    .mode-rag {
        background: linear-gradient(135deg, #2EC4B6 0%, #CBF3F0 100%);
        color: #1A1A2E;
    }

    .mode-search {
        background: linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)


def add_log(message: str, level: str = "INFO"):
    if "logs" not in st.session_state:
        st.session_state.logs = []
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append(f"[{timestamp}] {level}: {message}")
    if len(st.session_state.logs) > 20:
        st.session_state.logs = st.session_state.logs[-20:]


def get_vectorstore() -> VectorStoreManager:
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = VectorStoreManager()
    return st.session_state.vectorstore


def render_search_results(results):
    if not results:
        st.warning("Релевантные фрагменты не найдены")
        return

    for i, result in enumerate(results, 1):
        score_html = f'<span class="result-score">Score: {result.score:.3f}</span>' if result.score else ""

        st.markdown(f"""
        <div class="result-card">
            <div class="result-header">
                <span class="result-source">📄 {result.source} • Стр. {result.page}</span>
                {score_html}
            </div>
            <div class="result-text">{result.text}</div>
        </div>
        """, unsafe_allow_html=True)


def render_rag_response(response):
    # Основной ответ
    st.markdown(f"""
    <div class="answer-card">
        <div class="answer-title">💡 Ответ</div>
        <div class="answer-text">{response.answer}</div>
    """, unsafe_allow_html=True)

    # Источники
    if response.sources:
        sources_list = ", ".join([f"{s.source} (стр. {', '.join(map(str, s.pages))})" for s in response.sources])
        st.markdown(f"""
        <div class="sources-section">
            <div class="sources-title">📚 Источники</div>
            <div>{sources_list}</div>
        </div>
        """, unsafe_allow_html=True)

    # Цитаты
    if response.citations:
        st.markdown('<div class="sources-section"><div class="sources-title">📝 Цитаты</div>', unsafe_allow_html=True)
        for citation in response.citations:
            st.markdown(f"""
            <div class="citation-item">
                "{citation.text}"
                <div class="citation-source">— {citation.source}, стр. {citation.page}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Кнопка копирования
    with st.expander("📋 Копировать текст ответа"):
        st.code(response.answer, language=None)

    # Контекст
    if response.context_used:
        with st.expander("📄 Показать найденный контекст"):
            render_search_results(response.context_used)


# Page Header
st.markdown('<h1 class="page-title">💬 Чат</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">Задавайте вопросы по загруженным материалам</p>', unsafe_allow_html=True)

# Проверка индекса
vectorstore = get_vectorstore()
stats = vectorstore.get_stats()

if stats.is_empty():
    st.warning("⚠️ Индекс пуст!")
    st.markdown("""
    **Для начала работы:**
    1. Перейдите на страницу **Индексация**
    2. Загрузите PDF-файлы
    3. Нажмите **Построить индекс**
    """)
    st.stop()

# Режим работы
llm = LLMWrapper()
if llm.has_llm:
    st.markdown('<span class="mode-badge mode-rag">🤖 RAG режим — AI генерирует ответы</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="mode-badge mode-search">🔍 Режим поиска — без OpenAI ключа</span>', unsafe_allow_html=True)

# Поле ввода
top_k = st.session_state.get("top_k", 5)

query = st.text_area(
    "Введите ваш вопрос:",
    placeholder="Например: Что такое машинное обучение? Какие алгоритмы используются?",
    height=100,
    key="query_input"
)

# Кнопки
col1, col2 = st.columns(2)

with col1:
    search_button = st.button(
        "🔍 Найти фрагменты",
        disabled=not query,
        use_container_width=True
    )

with col2:
    if llm.has_llm:
        answer_button = st.button(
            "💡 Получить ответ",
            disabled=not query,
            type="primary",
            use_container_width=True
        )
    else:
        answer_button = False
        st.button(
            "💡 Требуется OpenAI",
            disabled=True,
            use_container_width=True
        )

# Обработка поиска
if search_button and query:
    add_log(f"Поиск: {query[:40]}...", "INFO")

    with st.spinner("🔍 Поиск релевантных фрагментов..."):
        retriever = Retriever(vectorstore)
        results = retriever.retrieve(query, top_k=top_k)

    st.markdown("---")
    if results:
        st.markdown(f"### Найдено {len(results)} фрагментов")
        render_search_results(results)
        add_log(f"Найдено {len(results)} результатов", "INFO")
    else:
        st.warning("Ничего не найдено. Попробуйте переформулировать вопрос.")

# Обработка генерации ответа
if answer_button and query:
    add_log(f"Генерация: {query[:40]}...", "INFO")

    with st.spinner("🧠 Анализ материалов и генерация ответа..."):
        retriever = Retriever(vectorstore)
        results, context = retriever.retrieve_with_context(query, top_k=top_k)

        if not results:
            st.warning("Релевантные фрагменты не найдены.")
        else:
            response = llm.generate_response(query, context, results)

            st.markdown("---")
            if response.is_search_only:
                st.warning("Режим поиска")
                render_search_results(results)
            else:
                render_rag_response(response)
                add_log("Ответ сгенерирован", "INFO")

# Подвал
st.markdown("---")
st.caption(f"📊 Индекс: {stats.num_documents} документов, {stats.num_chunks} фрагментов | top_k: {top_k}")
