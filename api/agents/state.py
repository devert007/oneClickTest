"""
AgentState — общее состояние, через которое все агенты обмениваются данными.

Каждый узел графа читает нужные поля и записывает результат.
LangGraph автоматически мержит возвращённый dict в текущий стейт.
"""

from __future__ import annotations
from typing import TypedDict, Optional


class AgentState(TypedDict, total=False):
    # ── Входные данные ──────────────────────────────────────────────
    user_input: str                     # текст запроса пользователя
    session_id: str                     # идентификатор сессии
    client_id: Optional[int]            # идентификатор пользователя/клиента
    model_name: str                     # имя LLM ("openai/gpt-oss-120b" и т.д.)
    chat_history: list                  # история [{role, content}, …]

    # ── Маршрутизация ───────────────────────────────────────────────
    agent_type: str                     # "rag" | "test_gen" | "chat"

    # ── RAG ─────────────────────────────────────────────────────────
    context: str                        # извлечённые чанки из ChromaDB

    # ── Генерация тестов ────────────────────────────────────────────
    test_params: Optional[dict]         # {question_count, difficulty, question_type, include_answers}
    document_text: Optional[str]        # полный текст документа для генерации

    # ── Результат ───────────────────────────────────────────────────
    final_answer: str                   # итоговый ответ агента
    error: Optional[str]               # описание ошибки (None если всё ок)
