"""
Промпты и конфигурация для генерации тестов.
Варианты: базовый, few-shot, chain-of-thought, multi-step.
"""

# Параметры модели по умолчанию (для Ollama / vLLM)
DEFAULT_LLM_CONFIG = {
    "temperature": 0.2,      # Низкая для детерминированного JSON
    "top_p": 0.9,
    "num_predict": 4096,
    "repeat_penalty": 1.1,
}

# Системный промпт для генератора (короткий, чёткий)
SYSTEM_PROMPT_GENERATOR = """Ты — эксперт по созданию учебных тестов. Генерируешь вопросы СТРОГО на основе предоставленного текста.
Правила:
1. Используй ТОЛЬКО факты из текста. Никаких внешних знаний.
2. Каждый вопрос — уникален, охватывает разную часть документа.
3. Неправильные варианты — правдоподобны, но явно неверны по тексту.
4. Минимум 3 варианта на вопрос. Один — правильный.
5. Возвращай ТОЛЬКО валидный JSON, без markdown и комментариев."""


def build_basic_prompt(
    document_text: str,
    question_count: int,
    difficulty: str,
    question_type: str,
    include_answers: bool,
) -> str:
    """Базовый промпт (текущий стиль, улучшенный)."""
    return f"""Сгенерируй тест на основе текста ниже.

ТЕКСТ ДОКУМЕНТА:
{document_text[:12000]}

ЗАДАЧА: Ровно {question_count} разных вопросов.
- Сложность: {difficulty}
- Тип: {question_type}
- Ответы: {"включить" if include_answers else "не включать"}

ФОРМАТ (строго JSON):
{{"questions": [
  {{"question": "...", "choices": ["A", "B", "C"], "answer": "A"}},
  ...
]}}

Верни ТОЛЬКО JSON, без ``` и пояснений."""


def build_few_shot_prompt(
    document_text: str,
    question_count: int,
    difficulty: str,
    question_type: str,
    include_answers: bool,
) -> str:
    """Промпт с few-shot примерами (лучше для малых моделей)."""
    example = '''
Пример (на основе абзаца "Python — язык программирования. Создан в 1991 году."):
{"questions": [
  {"question": "В каком году создан Python?", "choices": ["1989", "1991", "1995", "2000"], "answer": "1991"},
  {"question": "Python — это:", "choices": ["язык разметки", "язык программирования", "операционная система"], "answer": "язык программирования"}
]}
'''
    return f"""Сгенерируй тест по тексту. Следуй формату примера.

ТЕКСТ:
{document_text[:10000]}

Требуется: {question_count} вопросов. Сложность: {difficulty}. Ответы: {"да" if include_answers else "нет"}.
{example}

Твой JSON (только JSON):"""


def build_cot_prompt(
    document_text: str,
    question_count: int,
    difficulty: str,
    question_type: str,
    include_answers: bool,
) -> str:
    """Chain-of-Thought: сначала план, потом JSON (для более умных моделей)."""
    return f"""Сгенерируй тест по документу.

ТЕКСТ:
{document_text[:10000]}

Шаги:
1. Выдели {question_count} ключевых фактов/понятий из текста.
2. Для каждого сформулируй вопрос с 3–4 вариантами.
3. Убедись, что правильный ответ явно есть в тексте.
4. Верни JSON в формате: {{"questions": [{{"question":"...","choices":[...],"answer":"..."}}]}}

Сложность: {difficulty}. Ответы: {"включить" if include_answers else "не включать"}.

Сначала кратко перечисли факты (1–2 слова каждый), затем сразу JSON."""


def build_chunked_instruction(document_text: str, chunk: str, index: int, total: int) -> str:
    """Инструкция для генерации по одному чанку (multi-step архитектура)."""
    return f"""Чанк {index + 1} из {total}. Извлеки 1–2 вопроса с вариантами ответов.

ТЕКСТ ЧАНКА:
{chunk[:2000]}

Формат: {{"questions": [{{"question":"...","choices":["...","...","..."],"answer":"..."}}]}}
Только JSON."""
