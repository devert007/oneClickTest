import streamlit as st
from api_utils import upload_document, delete_document, list_documents, list_test_pdfs, delete_test_pdf, download_test_pdf,check_document_uniqueness
import uuid

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css("style.css")

def show_profile_page():
    st.sidebar.page_link("streamlit_app.py", label="Главная")
    st.sidebar.page_link("pages/generate_page.py", label="Сгенерировать тест")
    st.sidebar.page_link("pages/profile_page.py", label="Профиль")
    st.title("Профиль")

    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        
    st.header("Все материалы")
    
    if st.button("Обновить список документов"):
        with st.spinner("Обновление..."):
            st.session_state.documents = list_documents()
    
    if "documents" not in st.session_state:
        st.session_state.documents = list_documents()

    documents = st.session_state.documents
    if documents:
        for doc in documents:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.text(f"{doc['filename']}")
            
            with col2:
                if st.button(f"Удалить", key=f"delete_doc_{doc['id']}"):
                    with st.spinner(f"Удаление файла {doc['filename']}..."):
                        delete_response = delete_document(doc['id'])
                        if delete_response:
                            st.success(f"Файл {doc['filename']} удалён успешно.")
                            st.session_state.documents = list_documents()
                        else:
                            st.error(f"Ошибка при удалении файла {doc['filename']}.")

    else:
        st.write("Документов не найдено")

    st.header("Сохранённые PDF тесты")
    
    if st.button("Обновить список PDF тестов"):
        with st.spinner("Обновление..."):
            st.session_state.test_pdfs = list_test_pdfs()
    
    if "test_pdfs" not in st.session_state:
        st.session_state.test_pdfs = list_test_pdfs()

    test_pdfs = st.session_state.test_pdfs
    if test_pdfs:
        for pdf in test_pdfs:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.text(f"PDF Тест #{pdf['id']} (Документ: {pdf['document_id']}) - {pdf['filename']}")
            
            with col2:
                    pdf_content = download_test_pdf(pdf['id'])
                    if pdf_content:
                        st.download_button(
                            label="Скачать PDF",
                            data=pdf_content,
                            file_name=pdf['filename'],
                            mime="application/pdf",
                            key=f"download_button_{pdf['id']}"
                        )
                    else:
                        st.error(f"Ошибка при скачивании PDF теста {pdf['filename']}.")
            
            with col3:
                if st.button(f"Удалить", key=f"delete_pdf_{pdf['id']}"):
                    with st.spinner(f"Удаление PDF теста {pdf['filename']}..."):
                        delete_response = delete_test_pdf(pdf['id'])
                        if delete_response:
                            st.success(f"PDF тест {pdf['filename']} удалён успешно.")
                            st.session_state.test_pdfs = list_test_pdfs()
                        else:
                            st.error(f"Ошибка при удалении PDF теста {pdf['filename']}.")

    else:
        st.write("Сохранённых PDF тестов не найдено")

    

if __name__ == "__main__":
    show_profile_page()