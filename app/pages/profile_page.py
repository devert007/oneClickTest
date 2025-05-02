import streamlit as st
from api_utils import upload_document, delete_document, list_documents
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
    
    if st.button("Обновить список"):
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
                if st.button(f"Удалить", key=f"delete_{doc['id']}"):
                    with st.spinner(f"Удаление файла {doc['filename']}..."):
                        delete_response = delete_document(doc['id'])
                        if delete_response:
                            st.success(f"Файл {doc['filename']} удален успешно.")
                            st.session_state.documents = list_documents()
                        else:
                            st.error(f"Ошибка при удалении файла {doc['filename']}.")

    else:
        st.write("Документов не найдено")
    # st.header("Сгенерированные тесты")
    # if 'generated_test' in st.session_state:
    #     st.markdown(st.session_state.generated_test)


    st.header("Загрузить новый документ")
    uploaded_file = st.file_uploader("Выберите файл", type=["pdf", "docx", "html"])
    
    if uploaded_file is not None:
        if st.button("Загрузить"):
            with st.spinner("Загрузка..."):
                upload_response = upload_document(uploaded_file)
                if upload_response:
                    st.success(f"Файл '{uploaded_file.name}' загружен успешно с ID {upload_response['file_id']}.")
                    st.session_state.documents = list_documents() 
                else:
                    st.error("Ошибка загрузки файла.")
    
if __name__ == "__main__":
    show_profile_page()
