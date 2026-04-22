"""
Инструмент поиска по документам в ChromaDB.

Используется RAG-агентом и Test Generator агентом для получения
релевантных фрагментов из загруженных документов.
"""

import logging
from typing import Optional
from chroma_utils import vectorstore

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})


def search_documents(query: str, k: int = 3, client_id: Optional[int] = None) -> str:
    """
    Ищет в ChromaDB релевантные фрагменты по запросу.

    Args:
        query: поисковый запрос
        k: количество возвращаемых фрагментов

    Returns:
        Объединённый текст найденных фрагментов (или пустая строка).
    """
    try:
        search_filter = {"client_id": client_id} if client_id is not None else None
        if search_filter:
            docs = vectorstore.similarity_search(query, k=k, filter=search_filter)
        elif k != 3:
            local_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
            docs = local_retriever.invoke(query)
        else:
            docs = retriever.invoke(query)

        if not docs:
            return ""

        return "\n\n---\n\n".join(d.page_content for d in docs)

    except Exception as e:
        logging.error(f"search_documents error: {e}")
        return ""


def get_document_text_by_id(file_id: int, client_id: Optional[int] = None) -> str:
    """
    Получает полный текст документа из ChromaDB по file_id.

    Returns:
        Полный текст документа или пустая строка.
    """
    try:
        if client_id is not None:
            where_filter = {
                "$and": [
                    {"file_id": file_id},
                    {"client_id": client_id},
                ]
            }
            docs = vectorstore.get(where=where_filter)
            if docs and docs.get("documents"):
                return "\n\n".join(docs["documents"])

        docs = vectorstore.get(where={"file_id": file_id})
        if not docs or not docs.get("documents"):
            return ""
        return "\n\n".join(docs["documents"])
    except Exception as e:
        logging.error(f"get_document_text_by_id error: {e}")
        return ""
