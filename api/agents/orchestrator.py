"""
Orchestrator Agent — маршрутизирует запросы к нужному агенту.

Стратегия:
  1. Быстрые эвристики (есть test_params → test_gen)
  2. Если эвристики не сработали — LLM классифицирует intent
  3. Fallback → chat
"""

import logging
from agents.state import AgentState
from langchain_utils import create_llm

# Допустимые типы агентов
VALID_AGENTS = {"rag", "test_gen", "chat"}

ROUTING_PROMPT = """Ты — маршрутизатор запросов платформы OneClickTest.
Классифицируй запрос пользователя в ОДНУ из категорий:

- "rag"      → вопрос по загруженным документам, поиск информации в документах
- "test_gen" → генерация теста/викторины по документу
- "chat"     → общий разговор, вопросы о платформе, приветствие

Запрос пользователя: {user_input}

Ответь ТОЛЬКО одним словом (rag/test_gen/chat):"""


def orchestrator_node(state: AgentState) -> dict:
    """
    Определяет, какой агент должен обработать запрос.

    Приоритет:
      1. agent_type уже задан (напр. из API-эндпоинта) → пропускаем
      2. Есть test_params → test_gen
      3. LLM-классификация → rag/test_gen/chat
      4. Fallback → chat
    """
    # Если тип агента уже задан API-эндпоинтом — не меняем
    if state.get("agent_type"):
        return {"agent_type": state["agent_type"]}

    if state.get("test_params"):
        return {"agent_type": "test_gen"}

    # LLM-классификация
    user_input = state.get("user_input", "")
    model_name = state.get("model_name", "openai/gpt-oss-120b")

    try:
        llm = create_llm(model_name, temperature=0.0, max_tokens=10)
        response = llm.invoke(ROUTING_PROMPT.format(user_input=user_input))
        agent_type = response.content.strip().lower().replace('"', "").replace("'", "")

        if agent_type not in VALID_AGENTS:
            logging.warning(f"Orchestrator: unknown agent_type '{agent_type}', fallback to 'chat'")
            agent_type = "chat"

        logging.info(f"Orchestrator routed to: {agent_type}")
        return {"agent_type": agent_type}

    except Exception as e:
        logging.error(f"Orchestrator error: {e}, fallback to 'chat'")
        return {"agent_type": "chat"}


def route_to_agent(state: AgentState) -> str:
    """Функция условного ребра — возвращает имя следующего узла."""
    return state["agent_type"]
