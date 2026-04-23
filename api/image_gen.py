"""
Генерация иллюстраций для тестов.

Стратегия:
  1) Если вопрос про математическую функцию (парабола, синусоида и т.п.) —
     строим точный график через matplotlib.
  2) Иначе — просим Pollinations.ai сгенерировать схему (FLUX.1-schnell).
"""

import base64
import json
import logging
import os
import re
from io import BytesIO
from typing import Optional
from urllib.parse import quote

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import requests


POLLINATIONS_ENDPOINT = "https://image.pollinations.ai/prompt/"
DEFAULT_MODEL = "flux"

# Безопасный namespace для eval формулы (только numpy + аргумент x)
_SAFE_MATH_NAMES = {
    "np": np,
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
    "exp": np.exp, "log": np.log, "log10": np.log10, "log2": np.log2,
    "sqrt": np.sqrt, "abs": np.abs, "floor": np.floor, "ceil": np.ceil,
    "pi": np.pi, "e": np.e,
}

PLAN_PROMPT = """Ты — анализатор вопросов для тестов. Определи, нужен ли к вопросу график.

Если вопрос про математическую функцию (парабола, прямая, синусоида, гипербола и т.п.) или явно просит построить график y=f(x) — верни JSON:
{{"type":"function","function":"<формула через x в синтаксисе Python/NumPy>","x_range":[<min>,<max>],"title":"<краткий заголовок>","xlabel":"x","ylabel":"y"}}

Разрешено в формуле: x, числа, + - * / **, скобки, sin, cos, tan, exp, log, sqrt, abs, pi, e.
Примеры:
  "Парабола y = x^2"                → {{"type":"function","function":"x**2","x_range":[-5,5],"title":"y = x²","xlabel":"x","ylabel":"y"}}
  "График синуса"                   → {{"type":"function","function":"sin(x)","x_range":[-6.28,6.28],"title":"y = sin(x)","xlabel":"x","ylabel":"y"}}
  "Функция y = 2x + 3"              → {{"type":"function","function":"2*x + 3","x_range":[-10,10],"title":"y = 2x + 3","xlabel":"x","ylabel":"y"}}

Если графика явно не требуется, верни: {{"type":"none"}}

Вопрос:
{question}

Ответ — ТОЛЬКО ОДНОЙ строкой валидный JSON без пояснений и без markdown."""


def _parse_json_loose(text: str) -> Optional[dict]:
    """Вытаскивает JSON-объект из ответа LLM, игнорируя ```json обёртки."""
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def plan_chart_spec(question_text: str, llm) -> Optional[dict]:
    """Через LLM получает спецификацию графика или None."""
    if not question_text or llm is None:
        return None
    try:
        resp = llm.invoke(PLAN_PROMPT.format(question=question_text))
        content = getattr(resp, "content", None) or str(resp)
        spec = _parse_json_loose(content)
        if not spec:
            return None
        if spec.get("type") == "function" and spec.get("function"):
            return spec
        return None
    except Exception as e:
        logging.warning(f"plan_chart_spec failed: {e}")
        return None


def render_function_plot(spec: dict) -> Optional[str]:
    """Рисует matplotlib-график по спецификации. Возвращает data-URL (PNG)."""
    function_str = spec.get("function")
    if not function_str:
        return None

    x_range = spec.get("x_range") or [-5, 5]
    try:
        x_min, x_max = float(x_range[0]), float(x_range[1])
    except (TypeError, ValueError, IndexError):
        x_min, x_max = -5.0, 5.0
    if x_min >= x_max:
        x_min, x_max = -5.0, 5.0

    title = str(spec.get("title") or "")[:120]
    xlabel = str(spec.get("xlabel") or "x")[:20]
    ylabel = str(spec.get("ylabel") or "y")[:20]

    # Безопасный eval
    x = np.linspace(x_min, x_max, 400)
    names = dict(_SAFE_MATH_NAMES)
    names["x"] = x
    try:
        y = eval(function_str, {"__builtins__": {}}, names)
    except Exception as e:
        logging.warning(f"Cannot eval function '{function_str}': {e}")
        return None

    y = np.asarray(y, dtype=float)
    if y.shape != x.shape:
        y = np.full_like(x, float(y))

    fig, ax = plt.subplots(figsize=(6, 4), dpi=130)
    try:
        ax.plot(x, y, linewidth=2)
        ax.axhline(0, color="#888", linewidth=0.6)
        ax.axvline(0, color="#888", linewidth=0.6)
        ax.grid(True, alpha=0.3)
        if title:
            ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
    finally:
        plt.close(fig)

    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


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
    """Fallback: картинка через Pollinations.ai."""
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
    Главная точка входа: matplotlib → Pollinations.

    Args:
        question_text: текст вопроса
        llm: langchain LLM для классификации (если None, сразу fallback на Pollinations)
    """
    if llm is not None:
        spec = plan_chart_spec(question_text, llm)
        if spec:
            data_url = render_function_plot(spec)
            if data_url:
                return data_url
    return generate_pollinations_image(question_text)
