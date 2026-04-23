"""
LangGraph Agentic RAG — мульти-агентная система OneClickTest.

Архитектура:
    User → Orchestrator (Router) → RAG Agent
                                  → Test Generator Agent
                                  → Chat Agent
"""

from agents.graph import run_agent, get_graph

__all__ = ["run_agent", "get_graph"]
