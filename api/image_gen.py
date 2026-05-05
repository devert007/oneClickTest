"""
Генерация иллюстраций для тестов через Pollinations.ai (FLUX.1-schnell).
"""

import base64
import logging
import os
from typing import Optional
from urllib.parse import quote

import requests


POLLINATIONS_ENDPOINT = "https://image.pollinations.ai/prompt/"
DEFAULT_MODEL = "flux"


def _build_pollinations_prompt(topic: str) -> str:
    topic_clean = (topic or "").strip().replace("\n", " ")[:220]
    return (
        f"Educational schematic diagram illustrating: {topic_clean}. "
        "Clean minimalist infographic, white background, thin lines, "
        "labeled parts, vector style, no photorealism."
    )


def generate_pollinations_image(
    question_text: str,
    api_key: Optional[str] = None,
    width: int = 640,
    height: int = 480,
) -> Optional[str]:
    """Генерирует иллюстрацию через Pollinations.ai и возвращает data-URL."""
    token = api_key or os.getenv("POLLINATIONS_API_KEY") or os.getenv("POLLINATIONS_TOKEN")
    if not token:
        logging.warning("POLLINATIONS_API_KEY не задан — пропускаем генерацию картинки")
        return None

    prompt = _build_pollinations_prompt(question_text)
    url = POLLINATIONS_ENDPOINT + quote(prompt, safe="")

    try:
        resp = requests.get(
            url,
            params={
                "model": DEFAULT_MODEL,
                "width": width,
                "height": height,
                "nologo": "true",
                "safe": "true",
                "token": token,
            },
            headers={"Authorization": f"Bearer {token}"},
            timeout=90,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Pollinations image request failed: {e}")
        return None

    content_type = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
    if not content_type.startswith("image/"):
        logging.error(f"Pollinations returned non-image content-type: {content_type}")
        return None

    encoded = base64.b64encode(resp.content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def generate_chart_image(question_text: str, llm=None) -> Optional[str]:
    """
    Главная точка входа: генерация иллюстрации через Pollinations.ai.

    Args:
        question_text: текст вопроса
        llm: не используется (параметр сохранён для совместимости сигнатуры)
    """
    return generate_pollinations_image(question_text)
