import streamlit as st
from right_sidebar import display_sidebar
from chat_interface import display_chat_interface


def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Загружаем CSS из файла
load_css("style.css")


st.title("OneClickTest")
st.subheader("""OneClickTest - интеллектуальная платформа для автоматизированного создания тестов на основе учебных материалов, с интеграцией AI и поддержкой полного цикла работы с контентом.

Основное назначение:

Автоматизация процесса создания тестовых заданий из загруженных документов (лекций, методичек, статей) с использованием современных технологий AI (RAG-модели) и возможностью управления учебными материалами.
 
 
 Ключевые функции:
    -Загрузка материалов
    Поддержка форматов: PDF, DOCX. Документы индексируются в векторную базу ChromaDB для семантического поиска.

    -Генерация тестов
        Настройка параметров: количество вопросов, сложность, формат (множественный выбор/открытые вопросы)
        Интеграция с AI-моделями (Llama3.2)
        Автоматическое извлечение ключевых концепций из документов

    -Управление контентом
        Просмотр истории загруженных документов
        Удаление материалов
        Архивация сгенерированных тестов

    -Экспорт результатов
        Скачивание в форматах: Markdown, PDF
        Автоматическое форматирование с поддержкой кириллицы
        Генерация PDF с помощью ReportLab

    -Сессионная работа
        Сохранение истории чата
        Привязка тестов к сессиям и документам
        Многопользовательская поддержка через систему session_id""")

# Initialize session state variables
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

# Display the sidebar
display_sidebar()

# Display the chat interface
###display_chat_interface()