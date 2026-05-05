"""
Chat Agent — общение с пользователем о платформе OneClickTest.

Отвечает на вопросы о функционале, помогает разобраться
с интерфейсом и возможностями системы.
"""

import logging
from agents.state import AgentState
from langchain_utils import create_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

SYSTEM_PROMPT = (
    "Ты — AI-ассистент платформы OneClickTest. "
    "Помогаешь пользователям разобраться с функционалом.\n\n"
    "OneClickTest — интеллектуальная платформа для автоматизированного "
    "создания тестов на основе учебных материалов.\n\n"
    "Основные функции:\n"
    "• Помогаешь понять какие темы могут быть интересны для тестирования по ним учащихся\n"
    "• Загрузка учебных материалов (PDF, DOCX)\n"
    "• Автоматическая генерация тестов с помощью AI\n"
    "• Настройка параметров (сложность, тип вопросов, количество)\n"
    "• Анализ изображений с учебным контентом\n"
    "• Экспорт тестов (PDF, Google Forms)\n"
    "• Управление документами и историей тестов\n\n"
    "Будь вежливым, полезным и конкретным. "
    "Отвечай на том же языке, на котором задан вопрос."
)

CHAT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


def chat_node(state: AgentState) -> dict:
    """
    Узел Chat-агента в графе.

    Читает: user_input, chat_history, model_name
    Пишет:  final_answer
    """
    user_input = state.get("user_input", "")
    chat_history = state.get("chat_history", [])
    model_name = state.get("model_name", "openai/gpt-oss-120b")

    try:
        llm = create_llm(model_name, temperature=0.4, max_tokens=1024)
        chain = CHAT_PROMPT | llm | StrOutputParser()

        answer = chain.invoke({
            "input": user_input,
            "chat_history": chat_history,
        })

        return {"final_answer": answer}

    except Exception as e:
        logging.error(f"Chat Agent error: {e}")
        return {
            "final_answer": "Извините, чат временно недоступен. Попробуйте позже.",
            "error": str(e),
        }
