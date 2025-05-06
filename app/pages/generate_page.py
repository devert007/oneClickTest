import streamlit as st
from api_utils import upload_document, get_api_response, list_documents, upload_test_pdf
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

try:
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
except:
    st.warning("Не удалось загрузить шрифт Arial. Используется резервный шрифт.")

def markdown_to_pdf(markdown_text):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    try:
        p.setFont("Arial", 12)
    except:
        p.setFont("Helvetica", 12)

    lines = markdown_text.split("\n")
    y = 750
    line_height = 20

    for line in lines:
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

    st.header("1. Выберите или загрузите документ")
    
    documents = list_documents()
    
    if documents:
        doc_options = {doc['filename']: doc['id'] for doc in documents}
        selected_doc = st.selectbox(
            "Выберите из ранее загруженных документов",
            options=[""] + list(doc_options.keys())
        )
        
        if selected_doc:
            st.session_state.uploaded_file_id = doc_options[selected_doc]
            st.info(f"Выбран документ: {selected_doc}")

    uploaded_file = st.file_uploader(
        "Или загрузите новый файл",
        type=["pdf", "docx"],
        key="gen_uploader"
    )
    
    if uploaded_file and st.button("Загрузить файл"):
        with st.spinner("Идет загрузка..."):
            response = upload_document(uploaded_file)
            if response:
                st.session_state.uploaded_file_id = response['file_id']
                st.success(f"Документ {uploaded_file.name} успешно загружен!")
                documents = list_documents()

    st.header("2. Настройки теста")
    question_count = st.number_input("Количество вопросов", min_value=1, max_value=20, value=1)
    difficulty = st.select_slider("Уровень сложности", options=["Легкий", "Средний", "Сложный"])
    question_format = st.radio("Формат вопросов", ["Выбор варианта", "Открытый ответ", "Сбор правильного ответа из двух частей"])

    st.header("3. Сгенерировать тест")
    if st.button("Создать тест"):
        if 'uploaded_file_id' not in st.session_state:
            st.error("Сначала выберите или загрузите документ!")
            return

        prompt = f"""
        Сгенерируйте тест на основе документа. Требования:
        - Количество вопросов: {question_count}
        - Уровень сложности: {difficulty}
        - Формат вопросов: {question_format}
        - Включай правильные ответы (пиши правильные ответы в конце своего ответа, в таком формате [номер_вопроса].[ответ])
        - Используй информацию из последнего загруженного документа
        - Используй только тот язык, который используется в документе, но по возможности используй только русский и английский язык
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
                st.session_state.test_generated = True
                st.session_state.test_pdf = markdown_to_pdf(st.session_state.generated_test)
                st.success("Тест успешно сгенерирован!")


                pdf_response = upload_test_pdf(
                    pdf_buffer=st.session_state.test_pdf,
                    filename="generated_test.pdf",
                    document_id=st.session_state.uploaded_file_id,
                    session_id=st.session_state.session_id
                )
                if pdf_response:
                    st.success(f"PDF тест сохранён! ID: {pdf_response.get('file_id')}")
                else:
                    st.error("Ошибка сохранения PDF теста")
            else:
                st.error("Ошибка генерации теста")

    if 'test_generated' in st.session_state and st.session_state.test_generated and 'generated_test' in st.session_state:
        with st.expander("Просмотр теста", expanded=True):
            st.markdown(st.session_state.generated_test)

        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="Скачать MD",
                data=st.session_state.generated_test,
                file_name="generated_test.md",
                mime="text/markdown",
                key="download_md"
            )
        
        with col2:
            st.download_button(
                label="Скачать PDF",
                data=st.session_state.test_pdf,
                file_name="generated_test.pdf",
                mime="application/pdf",
                key="download_pdf"
            )
        
        # with col3:
        #     if st.button("Сохранить PDF тест", key="save_test"):
               

if __name__ == "__main__":
    show_generate_page()