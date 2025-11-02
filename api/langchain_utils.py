# langchain_utils.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from chroma_utils import vectorstore
from hugging_face_utils import hf_client
import logging
from typing import Dict, Any

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

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

def create_enhanced_test_prompt(question_type: str, difficulty: str, question_count: int) -> str:
    """Создает улучшенный промпт для генерации тестов"""
    
    difficulty_map = {
        "elementary": "ПРОСТОЙ УРОВЕНЬ: базовые понятия, простые формулировки",
        "middle": "СРЕДНИЙ УРОВЕНЬ: понимание основных концепций", 
        "high": "СЛОЖНЫЙ УРОВЕНЬ: анализ и синтез информации",
        "university": "ПРОФЕССИОНАЛЬНЫЙ УРОВЕНЬ: углубленные знания"
    }
    
    question_type_map = {
        "multiple_choice": "ВОПРОСЫ С ВЫБОРОМ ОТВЕТА (A, B, C, D)",
        "open_ended": "ОТКРЫТЫЕ ВОПРОСЫ (требуют развернутого ответа)"
    }
    
    base_prompt = f"""
    ТЫ - ЭКСПЕРТ ПО СОЗДАНИЮ ТЕСТОВ И УЧЕБНЫХ МАТЕРИАЛОВ

    ЗАДАЧА: Создать качественный тест на основе предоставленного контекста

    КРИТЕРИИ КАЧЕСТВА:
    - Уровень сложности: {difficulty_map.get(difficulty, difficulty)}
    - Тип вопросов: {question_type_map.get(question_type, question_type)}
    - Количество вопросов: {question_count}
    - Язык: Русский
    - Все вопросы ДОЛЖНЫ быть основаны ТОЛЬКО на предоставленном контексте

    СТРУКТУРА ТЕСТА:
    1. ВОПРОСЫ ({question_count} вопросов)
    2. РАЗДЕЛ "ПРАВИЛЬНЫЕ ОТВЕТЫ" в конце

    ТРЕБОВАНИЯ К ВОПРОСАМ:
    - Релевантность: каждый вопрос относится к ключевым идеям контекста
    - Ясность: формулировки четкие и однозначные
    - Баланс: сочетание разных аспектов темы

    ФОРМАТ ОТВЕТОВ:
    - Для вопросов с выбором: [номер]. [правильная_буква]
    - Для открытых вопросов: [номер]. [краткий_правильный_ответ]

    ВАЖНЫЕ ПРАВИЛА:
    - НЕ добавляй информацию вне контекста
    - НЕ пиши вступительные или заключительные фразы
    - Только вопросы и ответы!

    КОНТЕКСТ ДЛЯ ГЕНЕРАЦИИ:
    {{context}}

    Сгенерируй тест СТРОГО по указанным требованиям.
    """
    
    return base_prompt

class HuggingFaceChain:
    """Обертка для Hugging Face цепи"""
    
    def __init__(self, model: str, question_type: str, difficulty: str, question_count: int):
        self.model = model
        self.question_type = question_type
        self.difficulty = difficulty
        self.question_count = question_count
    
    def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            context = input_dict.get("context", "")
            chat_history = input_dict.get("chat_history", [])
            question = input_dict.get("input", "")
            
            # Создаем целевой промпт для генерации теста
            test_prompt = create_enhanced_test_prompt(
                self.question_type, 
                self.difficulty, 
                self.question_count
            )
            
            full_prompt = f"""
            {test_prompt}
            
            Контекст документа:
            {context}
            
            Дополнительные инструкции: {question}
            """
            
            # Вызываем Hugging Face API
            answer = hf_client.generate_text(full_prompt, self.model, max_length=2000, temperature=0.7)
            
            return {"answer": answer}
            
        except Exception as e:
            logging.error(f"Error in HuggingFace chain: {e}")
            return {"answer": "Извините, произошла ошибка при генерации теста."}

def get_rag_chain(model="deepseek-r1", question_type: str = "multiple_choice", 
                 difficulty: str = "middle", question_count: int = 5):
    """
    Возвращает RAG цепочку для генерации тестов с Hugging Face
    """
    return HuggingFaceChain(model, question_type, difficulty, question_count)

def get_simple_rag_chain(model="deepseek-r1"):
    """
    Простая RAG цепочка для обычных чат-запросов с Hugging Face
    """
    class SimpleHuggingFaceChain:
        def __init__(self, model: str):
            self.model = model
        
        def invoke(self, input_dict: Dict[str, Any]) -> Dict[str, Any]:
            try:
                context = input_dict.get("context", "")
                chat_history = input_dict.get("chat_history", [])
                question = input_dict.get("input", "")
                
                # Получаем релевантные чанки из базы знаний
                relevant_docs = vectorstore.as_retriever(search_kwargs={"k": 3}).get_relevant_documents(question)
                context_text = "\n\n".join([doc.page_content for doc in relevant_docs])
                
                full_prompt = f"""
На основе следующего контекста ответь на вопрос пользователя.

КОНТЕКСТ:
{context_text}

ВОПРОС: {question}

ОТВЕТЬ на русском языке строго на основе контекста. Если в контексте нет информации для ответа, скажи об этом.
"""
                
                answer = hf_client.generate_text(full_prompt, self.model, max_length=1500)
                return {"answer": answer}
                
            except Exception as e:
                logging.error(f"Error in SimpleHuggingFace chain: {e}")
                return {"answer": "Извините, произошла ошибка."}
    
    return SimpleHuggingFaceChain(model)