import streamlit as st
import sys
import os
import uuid
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.langchain_utils import get_chat_agent, SimpleChatHistory

def init_chat_agent():
    """Инициализирует чат-агента в session_state"""
    if 'chat_agent' not in st.session_state:
        st.session_state.chat_agent = get_chat_agent()
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = SimpleChatHistory()
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""

def toggle_chat():
    """Переключает состояние чата"""
    st.session_state.chat_open = not st.session_state.chat_open
    if st.session_state.chat_open:
        st.session_state.user_input = ""

def send_message():
    """Отправляет сообщение чат-агенту"""
    user_input = st.session_state.get('user_input_field', '').strip()
    print(st.session_state.get('user_input_field', ''))
    if not user_input:
        return
    
    st.session_state.chat_history.add_user_message(user_input)
    st.session_state.chat_messages.append({
        "role": "user", 
        "content": user_input,
        "time": datetime.now().strftime("%H:%M")
    })
    
    st.session_state.user_input = ""
    
    try:
        with st.spinner("🤔 Думаю..."):
            response = st.session_state.chat_agent.invoke({
                "input": user_input,
                "chat_history": st.session_state.chat_history.messages
            })
        
        ai_response = response.content if hasattr(response, 'content') else str(response)
        st.session_state.chat_history.add_ai_message(ai_response)
        st.session_state.chat_messages.append({
            "role": "assistant", 
            "content": ai_response,
            "time": datetime.now().strftime("%H:%M")
        })
        
        
    except Exception as e:
        error_msg = f"Извините, произошла ошибка: {str(e)}"
        st.session_state.chat_history.add_ai_message(error_msg)
        st.session_state.chat_messages.append({
            "role": "assistant", 
            "content": error_msg,
            "time": datetime.now().strftime("%H:%M")
        })

def clear_chat_history():
    """Очищает историю чата"""
    st.session_state.chat_history.clear()
    st.session_state.chat_messages = []

def render_chat_interface():
    """Рендерит интерфейс чат-агента"""
    
    st.markdown("""
    <style>
    /* Основной контейнер чата */
    
    
    /* Заголовок чата */
    .chat-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 13px 13px 0 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-weight: bold;
        font-size: 16px;
    }
    
    /* Область сообщений */
    .chat-messages-area {
        flex: 1;
        overflow-y: auto;
        background: #f8f9fa;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .stMain p {
    color: #000;
}
    /* Отдельное сообщение */
    .chat-message {
        padding: 12px 16px;
        border-radius: 18px;
        max-width: 85%;
        word-wrap: break-word;
        line-height: 1.4;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Сообщение пользователя */
    .user-message {
        background: #007bff;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,123,255,0.3);
    }
    
    /* Сообщение ассистента */
    .assistant-message {
        background: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-bottom-left-radius: 5px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Время сообщения */
    .message-time {
        font-size: 11px;
        opacity: 0.7;
        margin-top: 5px;
    }
    
    .user-message .message-time {
        text-align: right;
    }
    
    .assistant-message .message-time {
        text-align: left;
    }
    
    /* Область ввода */
    .chat-input-area {
        border-top: 1px solid #e0e0e0;
        background: white;
        border-radius: 0 0 13px 13px;
    }
    
    /* Кнопка переключения чата */
    .chat-toggle-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 50%;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        z-index: 1001;
        font-size: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .chat-toggle-btn:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* Кнопки в заголовке */
    .header-buttons {
        display: flex;
        gap: 8px;
        align-items: center;
    }
    
   
    
    /* Стили для кнопок в заголовке */
    .header-clear-btn, .header-close-btn {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        cursor: pointer;
        padding: 6px 12px;
        border-radius: 15px;
        font-size: 12px;
        transition: background-color 0.3s;
    }
    
    .header-clear-btn:hover, .header-close-btn:hover {
        background: rgba(255,255,255,0.3);
    }
    
    .header-close-btn {
        padding: 5px 10px;
        font-size: 16px;
    }
    .st-emotion-cache-ocqkz7{
                }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.chat_open:
        st.markdown("""
        <div style="position: fixed; bottom: 20px; right: 20px; z-index: 1001;">
        """, unsafe_allow_html=True)
        
        if st.button("💬", key="chat_toggle_btn", help="Открыть чат с ассистентом"):
            toggle_chat()
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.chat_open:
        st.markdown("""
        <div class="floating-chat-container">
            <div class="chat-header">
                <span></span>
                <div class="header-buttons">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.subheader("🤖 OneClickTest Assistant")

        with col2:
            if st.button("🗑️", key="clear_chat_btn", help="Очистить историю"):
                clear_chat_history()
                st.rerun()
        with col3:
            if st.button("❌", key="close_chat_btn", help="Закрыть чат"):
                st.session_state.chat_open = False
                st.rerun()
        
        st.markdown("""
                </div>
            </div>
            <div class="chat-messages-area" id="chatMessages">
        """, unsafe_allow_html=True)
        
        if not st.session_state.chat_messages:
            st.markdown(
                '<div style="text-align: center; color: #666; padding: 20px; font-style: italic;">Задайте вопрос о системе OneClickTest!</div>', 
                unsafe_allow_html=True
            )
        else:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    st.markdown(
                        f'''
                        <div class="chat-message user-message">
                            {msg["content"]}
                            <div class="message-time">{msg.get("time", "")}</div>
                        </div>
                        ''', 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'''
                        <div class="chat-message assistant-message">
                            {msg["content"]}
                            <div class="message-time">{msg.get("time", "")}</div>
                        </div>
                        ''', 
                        unsafe_allow_html=True
                    )
        
        st.markdown('</div>', unsafe_allow_html=True) 
        
        st.markdown('<div class="chat-input-area">', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            user_input = st.text_input(
                "Ваше сообщение",
                value=st.session_state.user_input,
                key="user_input_field",
                placeholder="Задайте вопрос о системе...",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("Отправить", key="send_btn", use_container_width=True):
                send_message()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True) 
        st.markdown('</div>', unsafe_allow_html=True)  
        
        st.markdown("""
        <script>
        // Автопрокрутка вниз
        setTimeout(() => {
            const messagesArea = document.getElementById('chatMessages');
            if (messagesArea) {
                messagesArea.scrollTop = messagesArea.scrollHeight;
            }
        }, 100);
        
       
        </script>
        """, unsafe_allow_html=True)

def handle_chat_interaction():
    """Обрабатывает взаимодействие с чатом"""
    init_chat_agent()
    
    render_chat_interface()