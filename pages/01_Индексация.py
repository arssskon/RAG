"""Страница индексации PDF файлов."""

import streamlit as st
from datetime import datetime
import time

from rag.pdf_loader import PDFLoader, validate_pdf
from rag.chunking import TextChunker
from rag.vectorstore import VectorStoreManager

st.set_page_config(page_title="Индексация | RAG Chat", page_icon="📤", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }

    .page-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .page-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }

    .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 2rem 0; }

    .stat-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
    }

    .stat-value { font-size: 2rem; font-weight: 800; color: #FF6B35; }
    .stat-label { font-size: 0.85rem; color: #666; text-transform: uppercase; letter-spacing: 1px; }

    .source-chip {
        display: inline-block;
        background: linear-gradient(135deg, #2EC4B6 0%, #CBF3F0 100%);
        color: #1A1A2E;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.9rem;
    }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: white; }

    .stButton > button { border-radius: 12px; font-weight: 600; transition: all 0.3s ease; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255,107,53,0.3); }
    .stAlert { border-radius: 12px; }
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


def process_pdf_files(uploaded_files, progress_bar, status_text):
    pdf_loader = PDFLoader()
    chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
    all_chunks = []
    total_files = len(uploaded_files)

    for idx, uploaded_file in enumerate(uploaded_files):
        filename = uploaded_file.name
        file_progress = (idx / total_files)

        status_text.markdown(f"📋 **Проверка:** {filename}")
        progress_bar.progress(file_progress + 0.1 / total_files)

        file_content = uploaded_file.read()
        is_valid, error_msg = validate_pdf(file_content)

        if not is_valid:
            add_log(f"Ошибка: {filename} - {error_msg}", "ERROR")
            st.error(f"❌ {filename}: {error_msg}")
            continue

        status_text.markdown(f"📖 **Парсинг:** {filename}")
        progress_bar.progress(file_progress + 0.3 / total_files)

        pages = pdf_loader.load_pdf(file_content, filename)

        if not pages:
            add_log(f"Нет текста: {filename}", "WARNING")
            continue

        add_log(f"Извлечено {len(pages)} страниц из {filename}", "INFO")

        status_text.markdown(f"✂️ **Разбиение:** {filename}")
        progress_bar.progress(file_progress + 0.6 / total_files)

        chunks = chunker.chunk_document(pages, filename)
        all_chunks.extend(chunks)
        add_log(f"Создано {len(chunks)} чанков из {filename}", "INFO")
        progress_bar.progress(file_progress + 0.9 / total_files)

    return all_chunks


def index_chunks(chunks, progress_bar, status_text, mode: str = "add"):
    vectorstore = get_vectorstore()

    if mode == "rebuild":
        status_text.markdown("🗑️ **Очистка старого индекса...**")
        progress_bar.progress(0.1)
        vectorstore.reset_index()
        st.session_state.vectorstore = VectorStoreManager()
        vectorstore = st.session_state.vectorstore
        add_log("Индекс очищен", "INFO")

    status_text.markdown("🧠 **Создание embeddings...**")
    progress_bar.progress(0.5)

    added_count = vectorstore.add_chunks(chunks)

    status_text.markdown("💾 **Сохранение в базу...**")
    progress_bar.progress(0.9)
    add_log(f"Добавлено {added_count} чанков", "INFO")
    progress_bar.progress(1.0)
    status_text.markdown("✅ **Готово!**")

    return added_count


# Page Header
st.markdown('<h1 class="page-title">📤 Индексация</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">Загрузите PDF-файлы для создания поискового индекса</p>', unsafe_allow_html=True)

# Текущая статистика
vectorstore = get_vectorstore()
stats = vectorstore.get_stats()

st.markdown(f"""
<div class="stats-grid">
    <div class="stat-card">
        <div class="stat-value">{stats.num_documents}</div>
        <div class="stat-label">Документов</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats.num_chunks}</div>
        <div class="stat-label">Фрагментов</div>
    </div>
    <div class="stat-card">
        <div class="stat-value">{stats.last_indexed.strftime('%d.%m') if stats.last_indexed else '—'}</div>
        <div class="stat-label">Обновлено</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Источники
if stats.sources:
    sources_html = "".join([f'<span class="source-chip">{src}</span>' for src in stats.sources])
    st.markdown(f"**Файлы в индексе:** {sources_html}", unsafe_allow_html=True)

st.markdown("---")

# Загрузка файлов
index_mode = st.session_state.get("index_mode", "add")

uploaded_files = st.file_uploader(
    "Перетащите PDF файлы или нажмите для выбора",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"Выбрано файлов: {len(uploaded_files)}")

col1, col2 = st.columns([2, 1])

with col1:
    build_button = st.button("🚀 Построить индекс", disabled=not uploaded_files, type="primary", use_container_width=True)

with col2:
    reset_button = st.button("🗑️ Очистить", type="secondary", use_container_width=True, disabled=stats.is_empty())

if reset_button:
    with st.spinner("Очистка..."):
        vectorstore.reset_index()
        st.session_state.vectorstore = VectorStoreManager()
        st.success("✅ Индекс очищен!")
        time.sleep(1)
        st.rerun()

if build_button and uploaded_files:
    st.markdown("---")
    st.markdown("### Процесс индексации")

    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        all_chunks = process_pdf_files(uploaded_files, progress_bar, status_text)

        if not all_chunks:
            st.error("❌ Не удалось извлечь текст")
        else:
            st.info(f"📊 Подготовлено: {len(all_chunks)} фрагментов")
            progress_bar.progress(0)
            added_count = index_chunks(all_chunks, progress_bar, status_text, index_mode)
            st.success(f"✅ Добавлено {added_count} фрагментов!")
            st.balloons()
            time.sleep(1.5)
            st.rerun()
    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")

# Логи
with st.expander("📋 Журнал", expanded=False):
    if "logs" in st.session_state and st.session_state.logs:
        for log in reversed(st.session_state.logs[-10:]):
            if "ERROR" in log:
                st.error(log)
            elif "WARNING" in log:
                st.warning(log)
            else:
                st.info(log)
    else:
        st.caption("Пусто")
