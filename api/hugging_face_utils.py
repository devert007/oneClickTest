# hugging_face_utils.py
import os
import logging
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

class HuggingFaceClient:
    def __init__(self):
        self.hf_token = os.getenv("HF_API_TOKEN")
        
        # Современные модели с поддержкой chat_completion
        self.working_models = {
    # Новые модели
    "smol-lm-3b": "HuggingFaceTB/SmolLM3-3B",
    "smol-lm-1.7b": "HuggingFaceTB/SmolLM2-1.7B",
    
    # Существующие модели
    "deepseek-r1": "deepseek-ai/DeepSeek-R1",
    "llama-3-70b": "meta-llama/Meta-Llama-3-70B-Instruct",
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "zephyr-7b": "HuggingFaceH4/zephyr-7b-beta",
    
    # Русскоязычные модели
    "russian-saiga": "IlyaGusev/saiga2_7b",
    "russian-gpt": "ai-forever/rugpt3large_based_on_gpt2",
    
    # Базовые модели (fallback)
    "gpt2": "gpt2",
    "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.2"
}

        
        # Приоритетная цепочка моделей
        self.priority_chain = [
            "smol-lm-3b",    # Легкая и эффективная модель
    "deepseek-r1",     # Самый мощный
    "llama-3-70b",     # Очень качественный
    "mixtral-8x7b",    # Хороший баланс
      
    "russian-saiga",   # Русскоязычный
    "zephyr-7b",       # Надежный
    "gpt2"             # Fallback
]
        # Инициализируем клиент
        self.client = InferenceClient(token=self.hf_token)
    
    def generate_text(self, prompt: str, model: str = "deepseek-r1", max_length: int = 2000, temperature: float = 0.7) -> str:
        """Генерация текста через современный chat_completion API"""
        try:
            model_name = self.working_models.get(model, model)
            
            logging.info(f"Generating text with model: {model_name}")
            
            # Используем новый chat_completion API
            response = self.client.chat_completion(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=temperature,
                # provider="auto"  # Автоматический выбор провайдера
            )
            
            # Извлекаем ответ
            if response and hasattr(response, 'choices') and len(response.choices) > 0:
                generated_text = response.choices[0].message.content.strip()
                logging.info(f"Successfully generated text: {generated_text[:100]}...")
                return generated_text
            else:
                logging.error(f"Unexpected response format: {response}")
                return self._try_fallback_chain(prompt, model)
                
        except Exception as e:
            error_msg = f"Hugging Face chat_completion error: {str(e)}"
            logging.error(error_msg)
            return self._try_fallback_chain(prompt, model)
    
    def _try_fallback_chain(self, prompt: str, failed_model: str = None) -> str:
        """Пробует использовать цепочку запасных моделей"""
        start_index = 0
        if failed_model:
            for i, model in enumerate(self.priority_chain):
                if model == failed_model:
                    start_index = i + 1
                    break
        
        for i in range(start_index, len(self.priority_chain)):
            fallback_model = self.priority_chain[i]
            logging.info(f"Trying fallback model {i+1}/{len(self.priority_chain)}: {fallback_model}")
            
            try:
                # Используем базовые параметры для fallback
                result = self.generate_text(
                    prompt=prompt,
                    model=fallback_model,
                    max_length=1500,
                    temperature=0.7
                )
                
                if result and not result.startswith("Ошибка"):
                    logging.info(f"Fallback model {fallback_model} succeeded")
                    return result
                    
            except Exception as e:
                logging.warning(f"Fallback model {fallback_model} also failed: {e}")
                continue
        
        error_msg = "Извините, все модели временно недоступны. Пожалуйста, попробуйте позже."
        logging.error("All models failed")
        return error_msg
    
    def get_available_models(self) -> list:
        """Возвращает список доступных моделей"""
        available_models = []
        
        for model_key, model_name in self.working_models.items():
            try:
                # Простая проверка доступности модели
                test_response = self.client.chat_completion(
                    model=model_name,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                available_models.append(model_key)
                logging.info(f"✓ Model {model_key} is available")
            except Exception as e:
                logging.warning(f"✗ Model {model_key} is unavailable: {e}")
        
        return available_models

# Глобальный клиент
hf_client = HuggingFaceClient()