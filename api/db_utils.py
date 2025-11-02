import psycopg2
from datetime import datetime
from typing import Tuple, List, Dict, Any, Optional
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получение параметров подключения из переменных окружения
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "rag_app")
DB_USER = os.getenv("DB_USER", "devert007")
DB_PASSWORD = os.getenv("DB_PASSWORD", "kislyCat.03")

def get_db_connection():
    """Создает и возвращает подключение к PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
    raise


def create_application_logs():
    """Создает таблицу для логов приложения"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS application_logs (
            id SERIAL PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_query TEXT NOT NULL,
            gpt_response TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Создаем индекс для улучшения производительности запросов по session_id
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_application_logs_session_id 
        ON application_logs(session_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_application_logs_created_at 
        ON application_logs(created_at)
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def create_document_store():
    """Создает таблицу для хранения документов"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_store (
            id SERIAL PRIMARY KEY,
            client_id INTEGER NOT NULL,
            filename TEXT NOT NULL UNIQUE,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Индекс для поиска по имени файла
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_store_filename 
        ON document_store(filename)
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def create_test_pdf_store():

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_pdf_store (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL,
            client_id INTEGER NOT NULL,
            document_id INTEGER,
            session_id TEXT NOT NULL,
            pdf_content BYTEA NOT NULL,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Индексы для улучшения производительности
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_pdf_store_session_id 
        ON test_pdf_store(session_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_pdf_store_document_id 
        ON test_pdf_store(document_id)
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def insert_application_logs(session_id: str, user_query: str, gpt_response: str, model: str) -> int:
    """Вставляет запись в логи приложения и возвращает ID вставленной записи"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO application_logs (session_id, user_query, gpt_response, model) VALUES (%s, %s, %s, %s) RETURNING id',
        (session_id, user_query, gpt_response, model)
    )
    log_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return log_id

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """Получает историю чата для указанной сессии"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_query, gpt_response FROM application_logs WHERE session_id = %s ORDER BY created_at',
        (session_id,)
    )
    messages = []
    for row in cursor.fetchall():
        messages.extend([
            {"role": "human", "content": row[0]},
            {"role": "ai", "content": row[1]}
        ])
    cursor.close()
    conn.close()
    return messages

def insert_document_record(filename: str, client_id: int = 0) -> int:
    """Вставляет запись о документе и возвращает ID файла"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO document_store (filename, client_id) VALUES (%s, %s) RETURNING id',
        (filename, client_id)
    )
    file_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return file_id

def insert_test_pdf_record(filename: str, document_id: int, session_id: str, pdf_content: bytes, client_id: int = 0) -> int:
    """Вставляет запись тестового PDF и возвращает ID файла"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO test_pdf_store (filename, document_id, session_id, pdf_content, client_id) VALUES (%s, %s, %s, %s, %s) RETURNING id',
        (filename, document_id, session_id, pdf_content, client_id)
    )
    file_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return file_id

def delete_document_record(file_id: int) -> bool:
    """Удаляет запись документа по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM document_store WHERE id = %s', (file_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def delete_test_pdf_record(file_id: int) -> bool:
    """Удаляет запись тестового PDF по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM test_pdf_store WHERE id = %s', (file_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return True

def get_all_documents() -> List[Dict[str, Any]]:
    """Получает все документы из хранилища"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, filename, upload_timestamp FROM document_store ORDER BY upload_timestamp DESC'
    )
    documents = []
    for row in cursor.fetchall():
        documents.append({
            'id': row[0],
            'filename': row[1],
            'upload_timestamp': row[2]
        })
    cursor.close()
    conn.close()
    return documents

def get_all_test_pdfs() -> List[Dict[str, Any]]:
    """Получает все тестовые PDF из хранилища"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, filename, document_id, session_id, upload_timestamp FROM test_pdf_store ORDER BY upload_timestamp DESC'
    )
    test_pdfs = []
    for row in cursor.fetchall():
        test_pdfs.append({
            'id': row[0],
            'filename': row[1],
            'document_id': row[2],
            'session_id': row[3],
            'upload_timestamp': row[4]
        })
    cursor.close()
    conn.close()
    return test_pdfs

def get_test_pdf_content(file_id: int) -> Optional[bytes]:
    """Получает содержимое тестового PDF по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT pdf_content FROM test_pdf_store WHERE id = %s', (file_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None

def check_filename_uniqueness(filename: str) -> Tuple[bool, str]:
    """
    Проверяет, существует ли файл с таким же именем в PostgreSQL.
    Возвращает: (is_unique, existing_filename)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT filename FROM document_store WHERE filename = %s', (filename,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return False, result[0]
        return True, ""
    except Exception as e:
        print(f"Error checking filename uniqueness: {e}")
        return False, f"Error: {str(e)}"

def initialize_database():
    """Инициализирует все таблицы в базе данных"""
    create_application_logs()
    create_document_store()
    create_test_pdf_store()
    print("Database tables initialized successfully")

# Инициализация базы данных при импорте модуля
if __name__ != "__main__":
    initialize_database()