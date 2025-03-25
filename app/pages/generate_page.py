import streamlit as st
from api_utils import upload_document, get_api_response, save_test
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Загружаем CSS из файла
load_css("style.css")
# Регистрируем шрифт с поддержкой кириллицы
try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
except:
    st.warning("Не удалось загрузить шрифт Arial. Используется резервный шрифт.")

def markdown_to_pdf(markdown_text):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Используем шрифт с поддержкой кириллицы
    try:
        p.setFont("Arial", 12)
    except:
        p.setFont("Helvetica", 12)  # Резервный шрифт

    lines = markdown_text.split("\n")
    y = 750  # Начальная позиция по Y
    line_height = 20

    for line in lines:
        # Разбиваем длинные строки
        while len(line) > 100:
            p.drawString(50, y, line[:100])
            line = line[100:]
            y -= line_height
        p.drawString(50, y, line)
        y -= line_height
        
        if y < 50:
            p.showPage()
            y = 750
            try:
                p.setFont("Arial", 12)
            except:
                p.setFont("Helvetica", 12)

    p.save()
    buffer.seek(0)
    return buffer

def show_generate_page():
    st.sidebar.page_link("streamlit_app.py", label="Главная")
    st.sidebar.page_link("pages/generate_page.py", label="Сгенерировать тест")
    st.sidebar.page_link("pages/profile_page.py", label="Профиль")
    st.title("Генерация тестов")

    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    # Загрузка документа
    st.header("1. Загрузите документ")
    uploaded_file = st.file_uploader("Выберите PDF или DOCX файл", type=["pdf", "docx"], key="gen_uploader")

    if uploaded_file and st.button("Загрузить файл"):
        with st.spinner("Идет загрузка..."):
            response = upload_document(uploaded_file)
            if response:
                st.session_state.uploaded_file_id = response['file_id']
                st.success(f"Документ {uploaded_file.name} успешно загружен!")

    # Настройки теста
    st.header("2. Настройки теста")

    question_count = st.number_input("Количество вопросов", min_value=1, max_value=20, value=1)
    difficulty = st.select_slider("Уровень сложности", options=["Легкий", "Средний", "Сложный"])
    question_format = st.radio("Формат вопросов", ["Выбор варианта", "Открытый ответ", "Сбор правильного ответа из двух частей"])

    # Генерация теста
    st.header("3. Сгенерировать тест")
    if st.button("Создать тест"):
        if 'uploaded_file_id' not in st.session_state:
            st.error("Сначала загрузите документ!")
            return

        prompt = f"""
        Сгенерируйте тест на основе документа. Требования:
        - Количество вопросов: {question_count}
        - Уровень сложности: {difficulty}
        - Формат вопросов: {question_format}
        - Включай правильные ответы (пиши правильныые ответы в конце своего ответа, в таком формате [номер_вопроса].[ответ])
        - Используй информацию из последнего загруженного документа
        - Используй только тот язык, который используется в документе, но по возможноси используй только русский и английский язык
        - Использовать только ту информацию, которая есть в загруженном документе
        """

        with st.spinner("Генерация теста..."):
            response = get_api_response(
                question=prompt,
                session_id=st.session_state.session_id,
                model="llama3.2"
            )

            if response:
                st.session_state.generated_test = response['answer']
                st.success("Тест успешно сгенерирован!")

                with st.expander("Просмотр теста"):
                    st.markdown(st.session_state.generated_test)

                # Секция экспорта
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Скачивание MD-файла
                    st.download_button(
                        label="Скачать MD",
                        data=st.session_state.generated_test,
                        file_name="generated_test.md",
                        mime="text/markdown"
                    )
                
                with col2:
                    # Конвертация PDF
                    pdf_buffer = markdown_to_pdf(st.session_state.generated_test)
                    st.download_button(
                        label="Скачать PDF",
                        data=pdf_buffer,
                        file_name="generated_test.pdf",
                        mime="application/pdf"
                    )
                
                with col3:
                    # Сохранение в базу данных
                    if st.button("Сохранить тест"):
                        save_response = save_test(
                            test_content=st.session_state.generated_test,
                            document_id=st.session_state.uploaded_file_id,
                            session_id=st.session_state.session_id
                        )
                        if save_response:
                            st.success(f"Тест сохранён! ID: {save_response.get('test_id')}")
                        else:
                            st.error("Ошибка сохранения теста")

            else:
                st.error("Ошибка генерации теста")

if __name__ == "__main__":
    show_generate_page()