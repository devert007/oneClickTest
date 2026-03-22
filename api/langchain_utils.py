# langchain_utils.py
import os
import logging
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from chroma_utils import vectorstore

from typing import List, Dict, Any

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

# ---------------------------------------------------------------------------
# LLM Factory — Groq (primary) + Ollama (fallback)
# ---------------------------------------------------------------------------

GROQ_MODELS = {
    "openai/gpt-oss-120b": "GPT-OSS 120B (Groq)",
}

LOCAL_MODEL = "bambucha/saiga-llama3:8b"


def create_groq_llm(model_name: str = "openai/gpt-oss-120b",
                     temperature: float = 0.2,
                     max_tokens: int = 4096):
    """Создает LLM через Groq API (удаленная модель)."""
    from langchain_groq import ChatGroq

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY не задан в .env")

    return ChatGroq(
        model=model_name,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_local_llm(temperature: float = 0.2,
                      max_tokens: int = 4096):
    """Создает LLM через локальный Ollama (fallback)."""
    from langchain_community.chat_models import ChatOllama

    return ChatOllama(
        model=LOCAL_MODEL,
        temperature=temperature,
        num_predict=max_tokens,
    )


def create_llm(model_name: str = "openai/gpt-oss-120b",
               temperature: float = 0.2,
               max_tokens: int = 4096):
    """
    Фабрика LLM.
    - USE_LOCAL_MODEL=true → всегда Ollama.
    - Модель из GROQ_MODELS → Groq, при ошибке fallback на Ollama.
    - Иначе → Ollama.
    """
    if USE_LOCAL_MODEL:
        logging.info("USE_LOCAL_MODEL=true → локальная модель Ollama")
        return create_local_llm(temperature, max_tokens)

    if model_name == LOCAL_MODEL:
        return create_local_llm(temperature, max_tokens)

    if model_name in GROQ_MODELS:
        try:
            llm = create_groq_llm(model_name, temperature, max_tokens)
            logging.info(f"Groq LLM создан: {model_name}")
            return llm
        except Exception as e:
            logging.warning(f"Groq недоступен ({e}), переключение на Ollama")
            return create_local_llm(temperature, max_tokens)

    return create_local_llm(temperature, max_tokens)


# ---------------------------------------------------------------------------
# Chat Agent
# ---------------------------------------------------------------------------

def get_chat_agent(model_name: str = "openai/gpt-oss-120b"):
    """Создает чат-агента для обсуждения системы OneClickTest"""
    try:
        llm = create_llm(model_name, temperature=0.3, max_tokens=1000)

        system_prompt = """
        Ты - AI-ассистент системы OneClickTest. Ты помогаешь пользователям разобраться с функционалом платформы.
        
        OneClickTest - это интеллектуальная платформа для автоматизированного создания тестов на основе учебных материалов.
        
        Основные функции системы:
        - Загрузка учебных материалов (PDF, DOCX)
        - Автоматическая генерация тестов с помощью AI
        - Настройка параметров теста (сложность, тип вопросов, количество)
        - Экспорт тестов в различные форматы (PDF, Word, Markdown)
        - Управление документами и историей тестов
        
        Будь вежливым, полезным и конкретным в ответах.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])

        chat_chain = prompt | llm
        return chat_chain

    except Exception as e:
        logging.error(f"Ошибка создания чат-агента: {e}")

        class FallbackChatAgent:
            def invoke(self, input_dict):
                return AIMessage(content="Извините, чат-агент временно недоступен. Пожалуйста, попробуйте позже.")

        return FallbackChatAgent()


# ---------------------------------------------------------------------------
# RAG Chain (реализована через LCEL, без langchain.chains)
# ---------------------------------------------------------------------------

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

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

qa_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Ты профессиональный генератор тестов. "
     "Создавай вопросы строго на основе предоставленного контекста.\n\n"
     "Контекст:\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}")
])


def get_rag_chain(model_name: str = "openai/gpt-oss-120b"):
    """Создает RAG цепочку с указанной моделью (Groq или Ollama fallback)."""
    try:
        print(f"Создание RAG цепи для модели: {model_name}")

        llm = create_llm(model_name, temperature=0.2, max_tokens=4096)
        print(f"LLM инициализирован: {type(llm).__name__}")

        contextualize_chain = contextualize_q_prompt | llm | StrOutputParser()
        answer_chain = qa_prompt | llm | StrOutputParser()

        class RAGChain:
            """RAG цепочка: переформулирование → поиск → генерация ответа."""

            def invoke(self, input_dict):
                user_input = input_dict.get("input", "")
                chat_history = input_dict.get("chat_history", [])

                # Переформулируем вопрос с учетом истории
                if chat_history:
                    query = contextualize_chain.invoke({
                        "input": user_input,
                        "chat_history": chat_history
                    })
                else:
                    query = user_input

                # Получаем релевантные документы
                docs = retriever.invoke(query)
                context = "\n\n".join(d.page_content for d in docs)

                # Генерируем ответ
                answer = answer_chain.invoke({
                    "context": context,
                    "chat_history": chat_history,
                    "input": user_input
                })

                return {"answer": answer}

        print("RAG цепь успешно создана")
        return RAGChain()

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА при создании RAG цепи: {e}")
        import traceback
        traceback.print_exc()
        logging.error(f"Ошибка создания RAG цепи: {e}")

        class FallbackChain:
            def invoke(self, input_dict):
                return {"answer": f"Извините, система временно недоступна. Ошибка: {str(e)}"}

        return FallbackChain()


# ---------------------------------------------------------------------------
# Startup check
# ---------------------------------------------------------------------------
try:
    if USE_LOCAL_MODEL:
        from langchain_community.chat_models import ChatOllama
        _test_llm = ChatOllama(model=LOCAL_MODEL)
        _test_resp = _test_llm.invoke("Привет")
        print("Локальная модель Ollama доступна!")
    else:
        _test_llm = create_groq_llm()
        _test_resp = _test_llm.invoke("Привет")
        print(f"Groq модель доступна! Ответ: {_test_resp.content[:80]}...")
except Exception as e:
    print(f"Предупреждение при проверке модели: {e}")
    print("Модель будет инициализирована при первом запросе.")
