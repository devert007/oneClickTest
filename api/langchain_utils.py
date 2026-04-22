"""
LLM Factory — единая фабрика для создания языковых моделей.

Поддерживает:
  • Groq Cloud (основной) — быстрый inference через API
  • Ollama (локальный fallback) — для работы без интернета

Все агенты импортируют create_llm() из этого модуля.
"""

import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

# ── Каталог доступных моделей ──────────────────────────────────────

GROQ_MODELS = {
    "openai/gpt-oss-120b": "GPT-OSS 120B (Groq)",
}

LOCAL_MODEL = "bambucha/saiga-llama3:8b"

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# ── Фабрики ────────────────────────────────────────────────────────

def create_groq_llm(
    model_name: str = "openai/gpt-oss-120b",
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> ChatGroq:
    """Создаёт LLM через Groq Cloud API."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY не задан в .env")

    return ChatGroq(
        model=model_name,
        api_key=GROQ_API_KEY,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def create_local_llm(
    temperature: float = 0.2,
    max_tokens: int = 4096,
) -> ChatOllama:
    """Создаёт LLM через локальный Ollama (fallback)."""
    return ChatOllama(
        model=LOCAL_MODEL,
        temperature=temperature,
        num_predict=max_tokens,
    )


def create_llm(
    model_name: str = "openai/gpt-oss-120b",
    temperature: float = 0.2,
    max_tokens: int = 4096,
):
    """
    Главная фабрика LLM.

    Логика выбора:
      1. USE_LOCAL_MODEL=true  → всегда Ollama
      2. model_name — локальная модель → Ollama
      3. model_name — модель Groq → Groq, при ошибке fallback на Ollama
      4. Всё остальное → Ollama
    """
    if USE_LOCAL_MODEL:
        logging.info("USE_LOCAL_MODEL=true → Ollama")
        return create_local_llm(temperature, max_tokens)

    if model_name == LOCAL_MODEL:
        return create_local_llm(temperature, max_tokens)

    if model_name in GROQ_MODELS:
        try:
            llm = create_groq_llm(model_name, temperature, max_tokens)
            logging.info(f"Groq LLM: {model_name}")
            return llm
        except Exception as e:
            logging.warning(f"Groq недоступен ({e}), fallback → Ollama")
            return create_local_llm(temperature, max_tokens)

    return create_local_llm(temperature, max_tokens)


# ── Проверка доступности при запуске ───────────────────────────────

try:
    if USE_LOCAL_MODEL:
        _test = ChatOllama(model=LOCAL_MODEL)
        _test.invoke("Привет")
        print("Ollama model available!")
    else:
        _test = create_groq_llm()
        _resp = _test.invoke("Привет")
        print(f"Groq model available! Response: {_resp.content[:80]}...")
except Exception as e:
    print(f"Model check warning: {e}")
    print("Model will be initialized on first request.")
