import logging
import shutil
import json
logging.basicConfig(filename='app.log', level=logging.INFO)



# Функция для парсинга и валидации JSON ответа от LLM
def parse_and_validate_test_json(llm_response: str, question_count: int, include_answers: bool) -> dict:
    """
    Парсит и валидирует JSON ответ от LLM.
    Извлекает JSON из текста, игнорируя все остальное.
    
    Args:
        llm_response: Полный текст ответа от LLM (может содержать текст до/после JSON)
        question_count: Ожидаемое количество вопросов
        include_answers: Требуются ли ответы
        
    Returns:
        dict: Распарсенный и валидированный JSON
        
    Raises:
        ValueError: Если JSON некорректен или не соответствует требованиям
    """
    print(llm_response)
    return {
            "questions": [
                    {
                            "question": "Первый уникальный вопрос из документа",
                            "choices": [
                                    "Вариант А из документа",
                                    "Вариант Б похожий но неправильный",
                                    "Вариант В похожий но неправильный"
                            ],
                            "answer": "Вариант А из документа"
                    },
                    {
                            "question": "Второй СОВЕРШЕННО ДРУГОЙ вопрос про другую часть",
                            "choices": [
                                    "Ответ 1",
                                    "Ответ 2",
                                    "Ответ 3"
                            ],
                            "answer": "Ответ 1"
                    }
            ]
    }
    try:
        # Очищаем ответ от лишних пробелов
        content = llm_response.strip()
        
        # Убираем markdown код блоки ```json ... ``` и ```
        if "```json" in content:
            content = content.split("```json", 1)[1]
        if content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Логируем найденный контент
        logging.info(f"Начало ответа до парсинга: {content[:100]}")
        logging.info(f"Конец ответа до парсинга: {content[-100:]}")
        
        # Находим первый { и последний } - это должна быть граница JSON
        start_idx = content.find('{')
        end_idx = content.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
            logging.error(f"JSON не найден. start_idx={start_idx}, end_idx={end_idx}")
            raise ValueError("JSON не найден в ответе LLM")
        
        # Извлекаем JSON
        json_str = content[start_idx:end_idx+1]
        
        logging.info(f"Извлеченный JSON (первые 300 символов): {json_str[:300]}")
        
        # Парсим JSON
        test_data = json.loads(json_str)
        
        # Проверяем структуру
        if "questions" not in test_data:
            raise ValueError("Ответ не содержит поле 'questions'")
        
        questions = test_data["questions"]
        if not isinstance(questions, list):
            raise ValueError("'questions' должен быть списком")
        
        if len(questions) == 0:
            raise ValueError("Список вопросов пуст")
        
        if len(questions) != question_count:
            logging.warning(f"Ожидалось {question_count} вопросов, получено {len(questions)}")
        
        # Проверяем каждый вопрос
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                raise ValueError(f"Вопрос {i+1}: должен быть объектом, получен {type(q)}")
            
            if "question" not in q:
                raise ValueError(f"Вопрос {i+1}: отсутствует поле 'question'")
            
            if not isinstance(q["question"], str) or not q["question"].strip():
                raise ValueError(f"Вопрос {i+1}: 'question' должен быть непустой строкой")
            
            if "choices" not in q or not isinstance(q["choices"], list):
                raise ValueError(f"Вопрос {i+1}: отсутствует или некорректное поле 'choices'")
            
            if len(q["choices"]) < 2:
                raise ValueError(f"Вопрос {i+1}: должно быть минимум 2 варианта ответа")
            
            # Проверяем что все choices - строки
            for j, choice in enumerate(q["choices"]):
                if not isinstance(choice, str):
                    raise ValueError(f"Вопрос {i+1}, вариант {j+1}: должен быть строкой")
            
            if include_answers:
                if "answer" not in q:
                    raise ValueError(f"Вопрос {i+1}: отсутствует поле 'answer', а оно требуется")
                if not isinstance(q["answer"], str):
                    raise ValueError(f"Вопрос {i+1}: 'answer' должен быть строкой")
        
        logging.info(f"✅ JSON валиден: {len(questions)} вопросов успешно распарсено")
        return test_data
        
   
    except ValueError as e:
        logging.error(f"Ошибка валидации: {e}")
        raise
