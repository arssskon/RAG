"""Страница О приложении."""

import streamlit as st
import os

st.set_page_config(page_title="О приложении | RAG Chat", page_icon="ℹ️", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1000px; }

    .page-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    .page-subtitle { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }

    .info-card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        margin-bottom: 1.5rem;
    }

    .info-card h3 {
        color: #FF6B35;
        margin-bottom: 1rem;
    }

    .flow-diagram {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border-radius: 20px;
        padding: 2rem;
        color: white;
        margin: 2rem 0;
        font-family: monospace;
        text-align: center;
    }

    .flow-box {
        display: inline-block;
        background: rgba(255,255,255,0.1);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 0.5rem;
        border: 1px solid rgba(255,255,255,0.2);
    }

    .flow-arrow {
        display: inline-block;
        color: #FF6B35;
        font-size: 1.5rem;
        margin: 0 0.5rem;
    }

    .tech-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .tech-item {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }

    .tech-name { font-weight: 700; color: #1A1A2E; }
    .tech-desc { font-size: 0.85rem; color: #666; }

    .tip-box {
        background: linear-gradient(135deg, #2EC4B6 0%, #CBF3F0 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .tip-box.warning {
        background: linear-gradient(135deg, #FF6B35 0%, #F7C59F 100%);
    }

    .status-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin: 1.5rem 0;
    }

    .status-item {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }

    .status-label { font-weight: 600; color: #1A1A2E; margin-bottom: 0.5rem; }
    .status-value { color: #666; }
    .status-value.ok { color: #2EC4B6; }
    .status-value.warn { color: #FF6B35; }

    [data-testid="stSidebar"] { background: linear-gradient(180deg, #1A1A2E 0%, #16213E 100%); }
    [data-testid="stSidebar"] .stMarkdown { color: white; }
</style>
""", unsafe_allow_html=True)

# Page Header
st.markdown('<h1 class="page-title">ℹ️ О приложении</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">Как работает RAG и советы по использованию</p>', unsafe_allow_html=True)

# Диаграмма работы
st.markdown("""
<div class="flow-diagram">
    <span class="flow-box">📝 Вопрос</span>
    <span class="flow-arrow">→</span>
    <span class="flow-box">🔍 Поиск</span>
    <span class="flow-arrow">→</span>
    <span class="flow-box">📚 Контекст</span>
    <span class="flow-arrow">→</span>
    <span class="flow-box">🤖 LLM</span>
    <span class="flow-arrow">→</span>
    <span class="flow-box">💡 Ответ</span>
</div>
""", unsafe_allow_html=True)

# Как работает
st.markdown("""
<div class="info-card">
    <h3>Как работает RAG?</h3>
    <p><strong>RAG (Retrieval-Augmented Generation)</strong> — технология, объединяющая поиск информации с генерацией текста.</p>

    <ol>
        <li><strong>Индексация:</strong> PDF разбиваются на фрагменты, преобразуются в векторы и сохраняются в базу</li>
        <li><strong>Поиск:</strong> Ваш вопрос преобразуется в вектор, находятся похожие фрагменты</li>
        <li><strong>Генерация:</strong> LLM получает вопрос + контекст и формирует ответ</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# Технологии
st.markdown("### Технологии")
st.markdown("""
<div class="tech-grid">
    <div class="tech-item">
        <div class="tech-name">Streamlit</div>
        <div class="tech-desc">Интерфейс</div>
    </div>
    <div class="tech-item">
        <div class="tech-name">ChromaDB</div>
        <div class="tech-desc">Векторная БД</div>
    </div>
    <div class="tech-item">
        <div class="tech-name">OpenAI</div>
        <div class="tech-desc">LLM & Embeddings</div>
    </div>
    <div class="tech-item">
        <div class="tech-name">LangChain</div>
        <div class="tech-desc">Оркестрация</div>
    </div>
    <div class="tech-item">
        <div class="tech-name">PyPDF</div>
        <div class="tech-desc">Парсинг PDF</div>
    </div>
    <div class="tech-item">
        <div class="tech-name">SentenceTransformers</div>
        <div class="tech-desc">Локальные embeddings</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Советы
st.markdown("### Советы по формулировке вопросов")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="tip-box">
        <strong>✅ Хорошие вопросы:</strong>
        <ul>
            <li>Конкретные и фокусированные</li>
            <li>С указанием темы или главы</li>
            <li>Про определения и сравнения</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="tip-box warning">
        <strong>❌ Проблемные вопросы:</strong>
        <ul>
            <li>Слишком общие</li>
            <li>Не по теме материалов</li>
            <li>Требующие внешних знаний</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Статус системы
st.markdown("---")
st.markdown("### Текущий статус")

has_openai = bool(os.getenv("OPENAI_API_KEY"))
has_chroma = os.path.exists("./chroma_store")

st.markdown(f"""
<div class="status-grid">
    <div class="status-item">
        <div class="status-label">OpenAI API</div>
        <div class="status-value {'ok' if has_openai else 'warn'}">
            {'✅ Подключен' if has_openai else '⚠️ Не настроен'}
        </div>
    </div>
    <div class="status-item">
        <div class="status-label">Хранилище ChromaDB</div>
        <div class="status-value {'ok' if has_chroma else 'warn'}">
            {'✅ Создано' if has_chroma else 'ℹ️ Будет создано при индексации'}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Настройка
with st.expander("⚙️ Настройка OpenAI"):
    st.code("""# Создайте файл .env в корне проекта:
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small""", language="bash")

st.markdown("---")
st.caption("RAG Chat по PDF-конспектам | MVP версия")
