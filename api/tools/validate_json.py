"""
Инструмент валидации JSON-структуры тестов.

Проверяет, что ответ LLM содержит корректный JSON
с правильной структурой: questions → [{question, choices, answer?}].
"""

from utils import parse_and_validate_test_json


def validate_test_json(
    raw_text: str,
    question_count: int,
    include_answers: bool,
) -> dict:
    """
    Парсит строку от LLM и валидирует структуру теста.

    Args:
        raw_text: сырой ответ LLM (может содержать markdown-обёртки)
        question_count: ожидаемое кол-во вопросов
        include_answers: нужны ли ответы в каждом вопросе

    Returns:
        dict с ключом "questions" — список валидных вопросов

    Raises:
        ValueError: если JSON невалиден
    """
    return parse_and_validate_test_json(raw_text, question_count, include_answers)
