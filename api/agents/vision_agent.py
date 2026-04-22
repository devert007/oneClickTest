"""
Vision Agent — анализ изображений через Llama 4 Scout (мультимодальная модель).

Используется модель meta-llama/llama-4-scout-17b-16e-instruct от Groq,
которая поддерживает анализ изображений (vision).

Возможности:
  - Описание содержимого изображения
  - Извлечение текста (OCR)
  - Анализ диаграмм, графиков, таблиц
  - Извлечение учебного контента из скриншотов/фото
"""

import os
import logging
from agents.state import AgentState
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# ── Конфигурация Vision-модели ──────────────────────────────────────
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

VISION_SYSTEM_PROMPT = (
    "Ты — эксперт по анализу изображений для образовательной платформы OneClickTest.\n\n"
    "Твои задачи:\n"
    "1. Подробно описать содержимое изображения\n"
    "2. Извлечь весь видимый текст\n"
    "3. Если изображение содержит учебный материал — выделить ключевые понятия\n"
    "4. Если это диаграмма/график/таблица — объяснить структуру и данные\n\n"
    "Отвечай на том же языке, на котором задан вопрос."
)


def create_vision_llm(temperature: float = 0.3, max_tokens: int = 2048) -> ChatGroq:
    """Создаёт мультимодальную LLM (Llama 4 Scout) через Groq API."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY не задан в .env")

    return ChatGroq(
        model=VISION_MODEL,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def vision_node(state: AgentState) -> dict:
    """
    Узел Vision-агента в графе.

    Читает: image_data, image_mime_type, user_input
    Пишет:  final_answer
    """
    image_data = state.get("image_data")
    user_input = state.get("user_input", "Опиши это изображение подробно.")
    mime_type = state.get("image_mime_type", "image/jpeg")

    if not image_data:
        return {
            "final_answer": "Изображение не предоставлено.",
            "error": "No image_data in state",
        }

    try:
        llm = create_vision_llm()

        # Формируем мультимодальное сообщение (текст + изображение)
        message = HumanMessage(content=[
            {
                "type": "text",
                "text": f"{VISION_SYSTEM_PROMPT}\n\nЗапрос пользователя: {user_input}",
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{image_data}",
                },
            },
        ])

        response = llm.invoke([message])
        return {"final_answer": response.content}

    except Exception as e:
        logging.error(f"Vision Agent error: {e}")
        return {
            "final_answer": f"Ошибка анализа изображения: {e}",
            "error": str(e),
        }
