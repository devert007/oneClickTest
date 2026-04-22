"""
RAG Agent — поиск по документам и генерация ответа.

Алгоритм:
  1. Переформулировать вопрос с учётом истории чата
  2. Найти релевантные фрагменты в ChromaDB
  3. Сгенерировать ответ на основе найденного контекста
"""

import logging
from agents.state import AgentState
from langchain_utils import create_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from tools.search_documents import search_documents

# ── Промпт для переформулирования вопроса ──────────────────────────
CONTEXTUALIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Учитывая историю чата и последний вопрос пользователя, "
     "сформулируй самостоятельный вопрос, понятный без контекста. "
     "НЕ отвечай — только переформулируй если нужно."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

# ── Промпт для генерации ответа ────────────────────────────────────
QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Ты — профессиональный ассистент. "
     "Отвечай на вопрос строго на основе предоставленного контекста. "
     "Если в контексте нет ответа — честно скажи об этом.\n\n"
     "Контекст:\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


def rag_node(state: AgentState) -> dict:
    """
    Узел RAG-агента в графе.

    Читает: user_input, chat_history, model_name
    Пишет:  final_answer, context
    """
    user_input = state.get("user_input", "")
    chat_history = state.get("chat_history", [])
    client_id = state.get("client_id")
    model_name = state.get("model_name", "openai/gpt-oss-120b")

    try:
        llm = create_llm(model_name, temperature=0.2, max_tokens=4096)
        contextualize_chain = CONTEXTUALIZE_PROMPT | llm | StrOutputParser()
        answer_chain = QA_PROMPT | llm | StrOutputParser()

        # Шаг 1: переформулируем вопрос (если есть история)
        query = user_input
        if chat_history:
            query = contextualize_chain.invoke({
                "input": user_input,
                "chat_history": chat_history,
            })

        # Шаг 2: поиск по ChromaDB
        context = search_documents(query, client_id=client_id)
        if not context:
            context = "(Релевантные документы не найдены)"

        # Шаг 3: генерация ответа
        answer = answer_chain.invoke({
            "context": context,
            "chat_history": chat_history,
            "input": user_input,
        })

        return {"final_answer": answer, "context": context}

    except Exception as e:
        logging.error(f"RAG Agent error: {e}")
        return {
            "final_answer": f"Ошибка RAG-агента: {e}",
            "error": str(e),
        }
