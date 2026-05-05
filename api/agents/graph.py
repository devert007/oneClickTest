"""
LangGraph — сборка графа агентов и главная точка входа.

Граф:
    ┌─────────────┐
    │ Orchestrator │  ← точка входа
    └──────┬──────┘
           │ conditional edge (route_to_agent)
     ┌─────┼──────────┐
     ▼     ▼          ▼
   [RAG] [TestGen] [Chat]
     │     │          │
     └─────┴──────────┘
                   │
                  END

Использование:
    from agents.graph import run_agent

    result = run_agent(
        user_input="Расскажи о фотосинтезе",
        session_id="abc-123",
        model_name="openai/gpt-oss-120b",
        chat_history=[...],
    )
    print(result["answer"])       # ответ агента
    print(result["agent_type"])   # какой агент обработал
"""

import logging
from typing import Optional

from langgraph.graph import StateGraph, END

from agents.state import AgentState
from agents.orchestrator import orchestrator_node, route_to_agent
from agents.rag_agent import rag_node
from agents.test_gen_agent import test_gen_node
from agents.chat_agent import chat_node


# ── Сборка графа ───────────────────────────────────────────────────

def build_graph():
    """Собирает и компилирует StateGraph со всеми агентами."""
    graph = StateGraph(AgentState)

    # Узлы
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("rag", rag_node)
    graph.add_node("test_gen", test_gen_node)
    graph.add_node("chat", chat_node)

    # Точка входа
    graph.set_entry_point("orchestrator")

    # рёбра: orchestrator → один из агентов
    graph.add_conditional_edges(
        "orchestrator",
        route_to_agent,
        {
            "rag": "rag",
            "test_gen": "test_gen",
            "chat": "chat",
        },
    )

    # Все агенты → END
    for node_name in ("rag", "test_gen", "chat"):
        graph.add_edge(node_name, END)

    return graph.compile()


# ── Ленивая инициализация ──────────────────────────────────────────

_compiled_graph = None


def get_graph():
    """Возвращает скомпилированный граф (создаёт при первом вызове)."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
        logging.info("Agent graph compiled successfully")
    return _compiled_graph


# ── Главная функция вызова ─────────────────────────────────────────

def run_agent(
    user_input: str,
    session_id: str = "",
    client_id: Optional[int] = None,
    model_name: str = "openai/gpt-oss-120b",
    chat_history: Optional[list] = None,
    agent_type: Optional[str] = None,
    test_params: Optional[dict] = None,
    document_text: Optional[str] = None,
) -> dict:
    """
    Главная точка входа — запускает граф агентов.

    Args:
        user_input:      текст запроса пользователя
        session_id:      ID сессии
        model_name:      имя LLM для генерации
        chat_history:    история чата
        agent_type:      принудительный выбор агента (None = оркестратор решает)
        test_params:     параметры генерации теста
        document_text:   текст документа для генерации теста

    Returns:
        dict: {
            "answer":     str   — ответ агента,
            "agent_type": str   — какой агент обработал,
            "error":      str|None — описание ошибки,
        }
    """
    # Формируем начальное состояние
    initial_state: dict = {
        "user_input": user_input,
        "session_id": session_id,
        "client_id": client_id,
        "model_name": model_name,
        "chat_history": chat_history or [],
    }

    if agent_type:
        initial_state["agent_type"] = agent_type
    if test_params:
        initial_state["test_params"] = test_params
    if document_text:
        initial_state["document_text"] = document_text

    try:
        graph = get_graph()
        result = graph.invoke(initial_state)

        return {
            "answer": result.get("final_answer", ""),
            "agent_type": result.get("agent_type", "unknown"),
            "error": result.get("error"),
        }

    except Exception as e:
        logging.error(f"Graph execution error: {e}")
        return {
            "answer": f"Системная ошибка: {e}",
            "agent_type": "error",
            "error": str(e),
        }
