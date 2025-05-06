import sqlite3
from datetime import datetime

DB_NAME = "rag_app.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_application_logs():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     session_id TEXT,
                     user_query TEXT,
                     gpt_response TEXT,
                     model TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def create_document_store():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS document_store
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     filename TEXT,
                     upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def create_test_pdf_store():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS test_pdf_store
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     filename TEXT,
                     document_id INTEGER,
                     session_id TEXT,
                     pdf_content BLOB,
                     upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.close()

def insert_application_logs(session_id, user_query, gpt_response, model):
    conn = get_db_connection()
    conn.execute('INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (?, ?, ?, ?)',
                 (session_id, user_query, gpt_response, model))
    conn.commit()
    conn.close()

def get_chat_history(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_query, gpt_response FROM application_logs WHERE session_id = ? ORDER BY created_at', (session_id,))
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row['user_query']},
            {"role": "ai", "content": row['gpt_response']}
        ])
    conn.close()
    return messages

def insert_document_record(filename):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO document_store (filename) VALUES (?)', (filename,))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id

def insert_test_pdf_record(filename, document_id, session_id, pdf_content):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO test_pdf_store (filename, document_id, session_id, pdf_content) VALUES (?, ?, ?, ?)',
                  (filename, document_id, session_id, pdf_content))
    file_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return file_id

def delete_document_record(file_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM document_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return True

def delete_test_pdf_record(file_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM test_pdf_store WHERE id = ?', (file_id,))
    conn.commit()
    conn.close()
    return True

def get_all_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC')
    documents = cursor.fetchall()
    conn.close()
    return [dict(doc) for doc in documents]

def get_all_test_pdfs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, document_id, session_id, upload_timestamp FROM test_pdf_store ORDER BY upload_timestamp DESC')
    test_pdfs = cursor.fetchall()
    conn.close()
    return [dict(pdf) for pdf in test_pdfs]

def get_test_pdf_content(file_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT pdf_content FROM test_pdf_store WHERE id = ?', (file_id,))
    result = cursor.fetchone()
    conn.close()
    return result['pdf_content'] if result else None



create_application_logs()
create_document_store()
create_test_pdf_store()