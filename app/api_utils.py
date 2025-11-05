import requests
import streamlit as st
import os
from io import BytesIO
# import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from auth_utils import get_current_client_id

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def get_api_response(question, session_id, model):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        "question": question,
        "model": model
    }
    if session_id:
        data["session_id"] = session_id

    try:
        response = requests.post("http://localhost:8000/chat", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API request failed with status code {response.status_code}: {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None
def upload_document(file):
    print("Uploading file...")
    try:
        files = {"file": (file.name, file, file.type)}
        
        # Получаем client_id текущего пользователя
        client_id = get_current_client_id()
        print(f"📝 Загрузка документа от client_id: {client_id}")
        
        # Добавляем client_id в данные формы
        data = {"client_id": client_id}
        
        response = requests.post("http://localhost:8000/upload-doc", files=files, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None
def get_document_text(file_id: int) -> str:
    print("file_id",file_id)
    if file_id is None:
        return ""
    
    try:
        response = requests.get(f"{API_BASE_URL}/get-document-text/{file_id}")
        if response.status_code == 200:
            return response.json().get("text", "")
        else:
            print(f"Error getting document text: {response.status_code} - {response.text}")
            return ""
    except Exception as e:
        print(f"Error getting document text: {e}")
        return ""

    
def upload_test_pdf(pdf_buffer: BytesIO, filename: str, document_id: int = None, session_id: str = None):
    print("Uploading test PDF...")
    try:
        files = {"file": (filename, pdf_buffer, "application/pdf")}
        data = {}
        if document_id:
            data["document_id"] = document_id
        else:
            data["document_id"] = 0
            
        if session_id:
            data["session_id"] = session_id
        else:
            data["session_id"] = "default_session"
        
        # Используем текущего клиента
        client_id = get_current_client_id()
        if client_id:
            data["client_id"] = client_id
        
        response = requests.post("http://localhost:8000/upload-test-pdf", files=files, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload test PDF. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the test PDF: {str(e)}")
        return None
def download_test_pdf(file_id: int):
    try:
        response = requests.get(f"http://localhost:8000/download-test-pdf/{file_id}")
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Failed to download test PDF. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while downloading the test PDF: {str(e)}")
        return None

def list_documents():
    try:
        # Передаем client_id в запрос
        client_id = get_current_client_id()
        response = requests.get(f"http://localhost:8000/list-docs?client_id={client_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
        return []

def list_test_pdfs():
    try:
        # Передаем client_id в запрос
        client_id = get_current_client_id()
        response = requests.get(f"http://localhost:8000/list-test-pdfs?client_id={client_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch test PDF list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the test PDF list: {str(e)}")
        return []

def delete_document(file_id):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {"file_id": file_id}

    try:
        response = requests.post("http://localhost:8000/delete-doc", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete document. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the document: {str(e)}")
        return None

def delete_test_pdf(file_id):
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {"file_id": file_id}

    try:
        response = requests.post("http://localhost:8000/delete-test-pdf", headers=headers, json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to delete test PDF. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while deleting the test PDF: {str(e)}")
        return None
def check_document_uniqueness(file):
    try:
        client_id = get_current_client_id()
        print("hi",client_id)
        files = {"file": (file.name, file, file.type)}
        data = {"client_id": client_id}
        response = requests.post("http://localhost:8000/check-uniqueness/", files=files,data=data)
        if response.status_code == 200:
            print(response,response.json())
            return response.json()
        else:
            st.error(f"Failed to check uniqueness. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while checking uniqueness: {str(e)}")
        return None


def generate_test_api(document_id: int, question_count: int, difficulty: str, question_type: str):
    """
    Вызов API для генерации теста с улучшенным промптом
    """
    try:
        data = {
            "document_id": document_id,
            "question_count": question_count,
            "difficulty": difficulty,
            "question_type": question_type
        }
        
        response = requests.post("http://localhost:8000/generate-test", json=data)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to generate test. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while generating test: {str(e)}")
        return None