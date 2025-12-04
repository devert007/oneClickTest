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
    raise e


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
            filename TEXT NOT NULL,
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
            UNIQUE(client_id, filename)  -- ИЗМЕНЕНИЕ: уникальность по паре (client_id, filename)
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_store_filename 
        ON document_store(filename)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_store_client_id 
        ON document_store(client_id)
    ''')
    conn.commit()
    cursor.close()
    conn.close()

def create_test_pdf_store():
    """Создает таблицу для тестовых PDF"""
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
            upload_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
            FOREIGN KEY (document_id) REFERENCES document_store(id) ON DELETE SET NULL
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_pdf_store_session_id 
        ON test_pdf_store(session_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_pdf_store_document_id 
        ON test_pdf_store(document_id)
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_pdf_store_client_id 
        ON test_pdf_store(client_id)
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

def insert_document_record(filename: str, client_id: int = None) -> int:
    """Вставляет запись о документе и возвращает ID файла"""
    if client_id is None:
        client_id = get_default_client_id()
        if client_id is None:
            raise Exception("Не найден клиент по умолчанию")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"📝 Вставка документа: {filename}, client_id: {client_id}")
        
        cursor.execute(
            'INSERT INTO document_store (filename, client_id) VALUES (%s, %s) RETURNING id',
            (filename, client_id)
        )
        file_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Document record inserted with ID: {file_id}")
        return file_id
    except Exception as e:
        print(f"❌ Error inserting document record: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def insert_test_pdf_record(filename: str, document_id: int, session_id: str, pdf_content: bytes, client_id: int = None) -> int:
    """Вставляет запись тестового PDF и возвращает ID файла"""
    if client_id is None:
        client_id = get_default_client_id()
        if client_id is None:
            raise Exception("Не найден клиент по умолчанию")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        print(f"📝 Вставка тестового PDF: filename={filename}, document_id={document_id}, client_id={client_id}")
        
        cursor.execute(
            'INSERT INTO test_pdf_store (filename, document_id, session_id, pdf_content, client_id) VALUES (%s, %s, %s, %s, %s) RETURNING id',
            (filename, document_id, session_id, pdf_content, client_id)
        )
        file_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Test PDF record inserted with ID: {file_id}")
        return file_id
    except Exception as e:
        print(f"❌ Error inserting test PDF record: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
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

def get_all_documents(client_id: int = None) -> List[Dict[str, Any]]:
    """Получает все документы из хранилища"""
    if client_id is None:
        client_id = get_default_client_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, filename, upload_timestamp, client_id FROM document_store WHERE client_id = %s ORDER BY upload_timestamp DESC',
        (client_id,)
    )
    documents = []
    for row in cursor.fetchall():
        documents.append({
            'id': row[0],
            'filename': row[1],
            'upload_timestamp': row[2],
            'client_id': row[3]  # ИЗМЕНЕНИЕ: Добавляем client_id
        })
    cursor.close()
    conn.close()
    print(f"📚 Получено документов для client_id {client_id}: {len(documents)}")
    return documents    

def get_all_test_pdfs(client_id: int = None) -> List[Dict[str, Any]]:
    """Получает все тестовые PDF из хранилища"""
    if client_id is None:
        client_id = get_default_client_id()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tps.id, tps.filename, tps.document_id, tps.session_id, 
               tps.upload_timestamp, tps.client_id, ds.filename as document_name
        FROM test_pdf_store tps
        LEFT JOIN document_store ds ON tps.document_id = ds.id
        WHERE tps.client_id = %s 
        ORDER BY tps.upload_timestamp DESC
    ''', (client_id,))
    
    test_pdfs = []
    for row in cursor.fetchall():
        test_pdfs.append({
            'id': row[0],
            'filename': row[1],
            'document_id': row[2],
            'session_id': row[3],
            'upload_timestamp': row[4],
            'client_id': row[5],  # Добавляем client_id
            'document_name': row[6]  
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

# В функции check_filename_uniqueness() в db_utils.py
def check_filename_uniqueness(filename: str, client_id: int = None) -> Tuple[bool, str]:
    """
    Проверяет, существует ли файл с таким же именем у данного клиента в PostgreSQL.
    Возвращает: (is_unique, existing_filename)
    """
    try:
        if client_id is None:
            client_id = get_default_client_id()
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT filename FROM document_store WHERE filename = %s AND client_id = %s', 
            (filename, client_id)
        )
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
    create_clients_table()
    create_application_logs()
    create_document_store()
    create_test_pdf_store()
    
    # Создаем клиента по умолчанию
    client_id = create_default_client()
    if client_id:
        print(f"✅ База данных инициализирована. Клиент по умолчанию: {client_id}")
    else:
        print("❌ Не удалось создать клиента по умолчанию")
    
    print("Database tables initialized successfully")


def create_client(username: str, email: str, password_hash: str) -> Optional[int]:
    """Создает нового клиента/пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO clients (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id',
            (username, email, password_hash)
        )
        client_id = cursor.fetchone()[0]
        conn.commit()
        return client_id
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()



def create_clients_table():
    """Создает таблицу клиентов с поддержкой аутентификации"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Сначала проверяем существующие колонки
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'clients' AND column_name = 'password_hash'
        """)
        has_password_hash = cursor.fetchone() is not None
        
        if not has_password_hash:
            # Добавляем недостающие колонки
            cursor.execute('ALTER TABLE clients ADD COLUMN password_hash TEXT NOT NULL DEFAULT %s', ('',))
            cursor.execute('ALTER TABLE clients ADD COLUMN is_active BOOLEAN DEFAULT TRUE')
            print("✅ Добавлены колонки password_hash и is_active в таблицу clients")
        
        # Создаем индексы если их нет
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clients_username 
            ON clients(username)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_clients_email 
            ON clients(email)
        ''')
        conn.commit()
        print("✅ Таблица clients готова для аутентификации")
        
    except Exception as e:
        print(f"❌ Ошибка при настройке таблицы clients: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_default_client():
    """Создает клиента по умолчанию (без пароля)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO clients (username, email, password_hash) VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING RETURNING id',
            ('default_user', 'default@example.com', '')
        )
        result = cursor.fetchone()
        conn.commit()
        if result:
            print(f"✅ Создан клиент по умолчанию с ID: {result[0]}")
            return result[0]
        else:
            # Получаем ID существующего клиента
            cursor.execute('SELECT id FROM clients WHERE username = %s', ('default_user',))
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

def get_default_client_id():
    """Получает ID клиента по умолчанию"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM clients WHERE username = %s', ('default_user',))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            # Если клиент не найден, создаем его
            return create_default_client()
    except Exception as e:
        print(f"❌ Ошибка получения client_id: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_client_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Получает клиента по имени пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, email, password_hash FROM clients WHERE username = %s AND is_active = TRUE', 
        (username,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2],
            'password_hash': result[3]
        }
    return None

def get_client_by_id(client_id: int) -> Optional[Dict[str, Any]]:
    """Получает клиента по ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, username, email FROM clients WHERE id = %s AND is_active = TRUE', 
        (client_id,)
    )
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'username': result[1],
            'email': result[2]
        }
    return None


# Инициализация базы данных при импорте модуля
if __name__ != "__main__":
    initialize_database()