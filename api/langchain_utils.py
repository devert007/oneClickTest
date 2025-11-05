# langchain_utils.py
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from chroma_utils import vectorstore
import logging

from langchain_core.messages import HumanMessage, AIMessage
from langchain.schema import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from typing import List, Dict, Any


class SimpleChatHistory(BaseChatMessageHistory):
    """Простая реализация истории чата для агента"""
    
    def __init__(self):
        self.messages = []
    
    def add_user_message(self, message: str) -> None:
        self.messages.append(HumanMessage(content=message))
    
    def add_ai_message(self, message: str) -> None:
        self.messages.append(AIMessage(content=message))
    
    def clear(self) -> None:
        self.messages.clear()
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        return self._messages
    
    @messages.setter
    def messages(self, value: List[Dict[str, Any]]) -> None:
        self._messages = value

def get_chat_agent():
    """Создает чат-агента для обсуждения системы OneClickTest"""
    try:
        llm = ChatOllama(
            model="lakomoor/vikhr-llama-3.2-1b-instruct:1b",
            temperature=0.3,
            num_predict=1000
        )
        
        # Системный промпт для агента поддержки
        system_prompt = """
        Ты - AI-ассистент системы OneClickTest. Ты помогаешь пользователям разобраться с функционалом платформы.
        
        OneClickTest - это интеллектуальная платформа для автоматизированного создания тестов на основе учебных материалов.
        
        Основные функции системы:
        - Загрузка учебных материалов (PDF, DOCX)
        - Автоматическая генерация тестов с помощью AI
        - Настройка параметров теста (сложность, тип вопросов, количество)
        - Интеграция с базой задач XML
        - Экспорт тестов в различные форматы (PDF, Word, Markdown)
        - Управление документами и историей тестов
        
        Твои задачи:
        1. Отвечать на вопросы о функционале системы
        2. Объяснять процесс работы с платформой
        3. Помогать с настройками генерации тестов
        4. Рассказывать о возможностях интеграции с XML базой задач
        5. Объяснять форматы экспорта и их особенности
        
        Будь вежливым, полезным и конкретным в ответах. Если не знаешь ответа - предложи обратиться к документации или попробовать соответствующий раздел интерфейса.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        
        # Создаем цепочку для чата
        chat_chain = prompt | llm
        
        return chat_chain
        
    except Exception as e:
        logging.error(f"Ошибка создания чат-агента: {e}")
        
        class FallbackChatAgent:
            def invoke(self, input_dict):
                return AIMessage(content="Извините, чат-агент временно недоступен. Пожалуйста, попробуйте позже.")
        
        return FallbackChatAgent()
    




retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Русский системный промпт для Vikhr модели
contextualize_q_system_prompt = (
    "Учитывая историю чата и последний вопрос пользователя, "
    "который может ссылаться на контекст в истории чата, "
    "сформулируй самостоятельный вопрос, который можно понять "
    "без истории чата. НЕ отвечай на вопрос, "
    "просто переформулируй его если нужно, или верни как есть."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

def get_rag_chain():
    """Создает RAG цепочку для Vikhr модели"""
    try:
        llm = ChatOllama(
            model="lakomoor/vikhr-llama-3.2-1b-instruct:1b",
            temperature=0.3,
            num_predict=2000
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты профессиональный генератор тестов. Создавай вопросы строго на основе предоставленного контекста."),
            ("system", "Контекст: {context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        return rag_chain
        
    except Exception as e:
        logging.error(f"Ошибка создания RAG цепи: {e}")
        # Простая fallback цепочка
        class FallbackChain:
            def invoke(self, input_dict):
                return {"answer": "Извините, система временно недоступна. Пожалуйста, попробуйте позже."}
        
        return FallbackChain()

# Проверка доступности модели при импорте
try:
    llm = ChatOllama(model="lakomoor/vikhr-llama-3.2-1b-instruct:1b")
    test_response = llm.invoke("Привет")
    print("✅ Модель Vikhr доступна!")
except Exception as e:
    print(f"❌ Модель Vikhr недоступна: {e}")