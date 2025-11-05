# langchain_utils.py
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from chroma_utils import vectorstore
import logging

retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# Русский системный промпт для Vikhr модели
contextualize_q_system_prompt = (
    "Учитывая историю чата и последний вопрос пользователя, "
    "который может ссылаться на контекст в истории чата, "
    "сформулируй самостоятельный вопрос, который можно понять "
    "без истории чата. НЕ отвечай на вопрос, "
    "просто переформулируй его если нужно, или верни как есть."
)

contextualize_q_prompt = ChatPromptTemplate.from_messages([
    ("system", contextualize_q_system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

def get_rag_chain():
    """Создает RAG цепочку для Vikhr модели"""
    try:
        llm = ChatOllama(
            model="lakomoor/vikhr-llama-3.2-1b-instruct:1b",
            temperature=0.3,
            num_predict=2000
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "Ты профессиональный генератор тестов. Создавай вопросы строго на основе предоставленного контекста."),
            ("system", "Контекст: {context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}")
        ])
        
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        return rag_chain
        
    except Exception as e:
        logging.error(f"Ошибка создания RAG цепи: {e}")
        # Простая fallback цепочка
        class FallbackChain:
            def invoke(self, input_dict):
                return {"answer": "Извините, система временно недоступна. Пожалуйста, попробуйте позже."}
        
        return FallbackChain()

# Проверка доступности модели при импорте
try:
    llm = ChatOllama(model="lakomoor/vikhr-llama-3.2-1b-instruct:1b")
    test_response = llm.invoke("Привет")
    print("✅ Модель Vikhr доступна!")
except Exception as e:
    print(f"❌ Модель Vikhr недоступна: {e}")