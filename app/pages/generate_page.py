import streamlit as st
from api_utils import upload_document, get_api_response
import uuid

import pdfkit
import markdown

def convert_md_to_pdf(md_text, output_filename):
    html_text = markdown.markdown(md_text)
    
    pdfkit.from_string(html_text, output_filename)

def show_generate_page():
    st.title("Генерация тестов")
    
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if 'test_params' not in st.session_state:
        st.session_state.test_params = {}
    
    # Секция загрузки документа
    st.header("1. Загрузите документ")
    uploaded_file = st.file_uploader("Выберите PDF или DOCX файл", 
                                   type=["pdf", "docx"],
                                   key="gen_uploader")
    
    if uploaded_file:
        if st.button("Загрузить файл"):
            with st.spinner("Идет загрузка..."):
                response = upload_document(uploaded_file)
                if response:
                    st.session_state.uploaded_file_id = response['file_id']
                    st.success(f"Документ {uploaded_file.name} успешно загружен!")

    # Параметры теста
    st.header("2. Настройки теста")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        question_count = st.number_input("Количество вопросов", 
                                       min_value=1, 
                                       max_value=20, 
                                       value=10)
    with col2:
        difficulty = st.select_slider("Уровень сложности", 
                                    options=["Легкий", "Средний", "Сложный"])
    with col3:
        question_format = st.radio("Формат вопросов", 
                                  ["Выбор варианта", "Открытый ответ"])
    
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
        - Включай правильные ответы
        - Используй только информацию из документа
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
                
                # Скачивание теста в формате MD
                st.download_button(
                    label="Скачать тест в формате MD",
                    data=st.session_state.generated_test,
                    file_name="generated_test.md",
                    mime="text/markdown"
                )
                
                # Конвертация и скачивание теста в формате PDF
                if st.button("Скачать тест в формате PDF"):
                    convert_md_to_pdf(st.session_state.generated_test, "generated_test.pdf")
                    with open("generated_test.pdf", "rb") as file:
                        st.download_button(
                            label="Скачать тест в формате PDF",
                            data=file,
                            file_name="generated_test.pdf",
                            mime="application/pdf"
                        )
            else:
                st.error("Ошибка генерации теста")


if __name__ == "__main__":
    show_generate_page()