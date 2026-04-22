"""
Test Generator Agent — генерация тестов с валидацией JSON.

Алгоритм:
  1. Построить промпт (few-shot) на основе текста документа и параметров
  2. Отправить в LLM (с контекстом из ChromaDB)
  3. Валидировать JSON-ответ
  4. При ошибке — повторить (до MAX_RETRIES раз)
"""

import json
import logging
from agents.state import AgentState
from langchain_utils import create_llm
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from tools.search_documents import search_documents
from tools.validate_json import validate_test_json
from test_generation_prompts import build_few_shot_prompt

MAX_RETRIES = 2

# ── Промпт для генерации теста ──────────────────────────────────────
TEST_GEN_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Ты — профессиональный генератор тестов. "
     "Создавай вопросы строго на основе предоставленного контекста.\n\n"
     "Контекст:\n{context}"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


def test_gen_node(state: AgentState) -> dict:
    """
    Узел Test Generator агента в графе.

    Читает: document_text, test_params, model_name, chat_history
    Пишет:  final_answer (JSON-строка с тестом)
    """
    model_name = state.get("model_name", "openai/gpt-oss-120b")
    chat_history = state.get("chat_history", [])
    client_id = state.get("client_id")
    test_params = state.get("test_params", {})
    document_text = state.get("document_text", "")

    # Извлекаем параметры теста
    question_count = test_params.get("question_count", 5)
    difficulty = test_params.get("difficulty", "Для средних классов")
    question_type = test_params.get("question_type", "multiple_choice")
    include_answers = test_params.get("include_answers", True)

    if not document_text:
        return {
            "final_answer": json.dumps(
                {"error": "Текст документа не предоставлен"},
                ensure_ascii=False,
            ),
            "error": "No document_text",
        }

    try:
        llm = create_llm(model_name, temperature=0.2, max_tokens=4096)
        answer_chain = TEST_GEN_PROMPT | llm | StrOutputParser()

        # Строим few-shot промпт
        prompt = build_few_shot_prompt(
            document_text=document_text,
            question_count=question_count,
            difficulty=difficulty,
            question_type=question_type,
            include_answers=include_answers,
        )

        # Дополнительный контекст из ChromaDB
        context = search_documents(prompt[:200], client_id=client_id)
        if not context:
            context = document_text[:3000]

        # Генерация + валидация с ретраями
        last_error = None
        for attempt in range(MAX_RETRIES):
            raw_answer = answer_chain.invoke({
                "context": context,
                "chat_history": chat_history,
                "input": prompt,
            })

            try:
                test_data = validate_test_json(raw_answer, question_count, include_answers)
                return {
                    "final_answer": json.dumps(test_data, ensure_ascii=False, indent=2),
                }
            except ValueError as e:
                last_error = e
                logging.warning(
                    f"Test JSON validation failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )

        # Все попытки исчерпаны — возвращаем сырой ответ
        return {
            "final_answer": raw_answer,
            "error": f"Validation failed after {MAX_RETRIES} attempts: {last_error}",
        }

    except Exception as e:
        logging.error(f"Test Generator Agent error: {e}")
        return {
            "final_answer": json.dumps({"error": str(e)}, ensure_ascii=False),
            "error": str(e),
        }
