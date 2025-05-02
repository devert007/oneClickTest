import requests
import streamlit as st
import os
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
        response = requests.post("http://localhost:8000/upload-doc", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload file. Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"An error occurred while uploading the file: {str(e)}")
        return None

def list_documents():
    try:
        response = requests.get("http://localhost:8000/list-docs")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch document list. Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        st.error(f"An error occurred while fetching the document list: {str(e)}")
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
# app/api_utils.py

def save_test(test_content, document_id=None, session_id=None):
    try:
        response = requests.post(
            f"{API_BASE_URL}/save-test",
            json={
                "test_content": test_content,
                "document_id": document_id,
                "session_id": session_id
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Save Test Error: {str(e)}")
        return None

def list_tests():
    try:
        response = requests.get(f"{API_BASE_URL}/list-tests")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"List Tests Error: {str(e)}")
        return []

def delete_test(test_id):
    try:
        response = requests.post(
            f"{API_BASE_URL}/delete-test",
            json={"test_id": test_id}
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Delete Test Error: {str(e)}")
        return False


