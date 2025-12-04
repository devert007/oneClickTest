# auth_utils.py - исправленные импорты
import streamlit as st
import hashlib
import secrets
import sys
import os

# Добавляем путь к папке api для импорта
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.db_utils import get_client_by_username, create_client, get_client_by_id, get_default_client_id

def hash_password(password: str) -> str:
    """Хеширует пароль"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет пароль"""
    return hash_password(password) == hashed_password

def init_session_state():
    """Инициализирует состояние сессии"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'client_id' not in st.session_state:
        st.session_state.client_id = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None

def login_user(username: str, password: str) -> bool:
    """Аутентифицирует пользователя"""
    try:
        client = get_client_by_username(username)
        if client and verify_password(password, client['password_hash']):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.client_id = client['id']
            st.session_state.session_id = f"{client['id']}_{secrets.token_hex(8)}"
            return True
        return False
    except Exception as e:
        st.error(f"Ошибка авторизации: {e}")
        return False

def register_user(username: str, email: str, password: str) -> bool:
    """Регистрирует нового пользователя"""
    try:
        # Проверяем, не существует ли уже пользователь
        if get_client_by_username(username):
            return False
        
        password_hash = hash_password(password)
        client_id = create_client(username, email, password_hash)
        
        if client_id:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.client_id = client_id
            st.session_state.session_id = f"{client_id}_{secrets.token_hex(8)}"
            return True
        return False
    except Exception as e:
        st.error(f"Ошибка регистрации: {e}")
        return False

def logout_user():
    """Выход пользователя"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.client_id = None
    st.session_state.session_id = None
    if "messages" in st.session_state:
        st.session_state.messages = []

def require_auth():
    """Проверяет аутентификацию, если не авторизован - показывает форму входа"""
    init_session_state()
    
    if not st.session_state.authenticated:
        show_auth_page()
        st.stop()

def show_auth_page():
    """Показывает страницу аутентификации"""
    st.markdown("""
        <style>
        .auth-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 OneClickTest - Авторизация")
    
    tab1, tab2 = st.tabs(["Вход", "Регистрация"])
    
    with tab1:
        st.header("Вход в систему")
        with st.form("login_form"):
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            submit = st.form_submit_button("Войти")
            
            if submit:
                if not username or not password:
                    st.error("Заполните все поля")
                elif login_user(username, password):
                    st.success(f"Добро пожаловать, {username}!")
                    st.rerun()
                else:
                    st.error("Неверное имя пользователя или пароль")
    
    with tab2:
        st.header("Регистрация")
        with st.form("register_form"):
            new_username = st.text_input("Новое имя пользователя", placeholder="От 3 до 20 символов")
            new_email = st.text_input("Email", placeholder="your@email.com")
            new_password = st.text_input("Новый пароль", type="password", placeholder="Минимум 6 символов")
            confirm_password = st.text_input("Подтвердите пароль", type="password")
            submit_register = st.form_submit_button("Зарегистрироваться")
            
            if submit_register:
                if not new_username or not new_email or not new_password:
                    st.error("Все поля обязательны для заполнения")
                elif len(new_username) < 3:
                    st.error("Имя пользователя должно содержать минимум 3 символа")
                elif len(new_password) < 6:
                    st.error("Пароль должен содержать минимум 6 символов")
                elif new_password != confirm_password:
                    st.error("Пароли не совпадают")
                elif "@" not in new_email:
                    st.error("Введите корректный email")
                else:
                    if register_user(new_username, new_email, new_password):
                        st.success("Регистрация успешна! Добро пожаловать!")
                        st.rerun()
                    else:
                        st.error("Пользователь с таким именем уже существует")

def get_current_client_id():
    """Возвращает ID текущего клиента или клиента по умолчанию если не авторизован"""
    if st.session_state.get('authenticated') and st.session_state.get('client_id'):
        return st.session_state.client_id
    else:
        # Возвращаем ID клиента по умолчанию для неавторизованных пользователей
        return get_default_client_id()