import json
from typing import Union, Dict, List, Any

def test_json_to_markdown(test_content: Union[str, Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """
    Convert a test JSON into a Markdown string with questions (without answers)
    and a separate "Answers" section at the end.

    Args:
        test_content: Can be:
            - a JSON string
            - a dict with a "questions" key containing a list of questions
            - a list of question dicts directly

    Returns:
        A Markdown formatted string with the test and answers section.
    """
    # 1. Parse input if it's a string (assume JSON)
    if isinstance(test_content, str):
        try:
            data = json.loads(test_content)
        except json.JSONDecodeError:
            # If it's not valid JSON, return as is (maybe it's already markdown)
            return test_content
    else:
        data = test_content

    # 2. Normalize to a list of question dicts
    if isinstance(data, dict) and "questions" in data:
        questions = data["questions"]
    elif isinstance(data, list):
        questions = data
    else:
        # Unexpected format: return string representation
        return str(data)

    if not questions:
        return "# Тест\n\nТест пуст."

    # 3. Build markdown
    lines = ["# Тест", ""]
    answers = []  # store (question_number, answer_text) for the answers section

    for i, q in enumerate(questions, 1):
        question_text = q.get("question", "No question text")
        choices = q.get("choices", [])
        correct = q.get("answer", "")

        # Store answer for later
        answers.append((i, correct))

        lines.append(f"## Вопрос {i}")
        lines.append(question_text)
        lines.append("")

        if choices:
            for choice in choices:
                lines.append(f"- {choice}")
        else:
            # No choices – just show the question, answer will appear in answers section
            lines.append("*Ответ будет указан в конце.*")
        lines.append("")  # blank line between questions

    # Add answers section
    lines.append("---")
    lines.append("## Ответы")
    lines.append("")
    for num, ans in answers:
        lines.append(f"**Вопрос {num}:** {ans}")

    return "\n".join(lines)