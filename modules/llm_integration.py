# llm_integration.py
import time
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from openai import OpenAI
from modules.api_utils import APIUtils


class LLMServiceProvider:
    """
    Класс для работы с различными LLM сервисами через единый интерфейс.
    Поддерживает DeepSeek, OpenAI и другие API-совместимые сервисы.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        """
        Инициализирует клиент для работы с LLM сервисом.
        
        Args:
            api_key (str): API ключ для доступа к сервису
            base_url (str): Базовый URL API (по умолчанию DeepSeek)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        # Инициализация логгера
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def get_model_list(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных моделей.
        
        Returns:
            List[Dict[str, Any]]: Список моделей с их параметрами
        """
        try:
            # Для DeepSeek
            if "deepseek" in self.base_url:
                return [
                    {"id": "deepseek-chat", "name": "DeepSeek Chat", "context_length": 4096},
                    {"id": "deepseek-coder", "name": "DeepSeek Coder", "context_length": 8192}
                ]
            # Для OpenAI
            elif "openai" in self.base_url:
                response = self.client.models.list()
                return [{"id": model.id, "name": model.id, "created": model.created} for model in response.data]
            else:
                # Для других провайдеров - заглушка
                return [{"id": "default-model", "name": "Default Model", "context_length": 4096}]
        except Exception as e:
            print(f"Ошибка при получении списка моделей: {e}")
            return [{"id": "deepseek-chat", "name": "DeepSeek Chat (fallback)", "context_length": 4096}]
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 300,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        max_retries: int = 5,
        retry_delay: int = 1
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Выполняет запрос к API модели с механизмом повторных попыток.
        
        Args:
            messages (List[Dict[str, str]]): Список сообщений для отправки
            model (str): ID модели
            temperature (float): Параметр температуры
            max_tokens (int): Максимальное количество токенов в ответе
            top_p (float): Параметр top_p
            frequency_penalty (float): Штраф за повторение
            presence_penalty (float): Штраф за наличие
            max_retries (int): Максимальное количество повторных попыток
            retry_delay (int): Начальная задержка между попытками в секундах
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (ответ, ошибка)
        """
        def _make_request() -> Tuple[Optional[str], Optional[str]]:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stream=False
                )
                
                # Правильно извлекаем ответ
                return response.choices[0].message.content.strip(), None
                    
            except Exception as e:
                return None, f"Ошибка API: {str(e)}"
        
        # Использование APIUtils для повторных попыток
        return APIUtils.retry_with_backoff(
            _make_request,
            max_retries=max_retries,
            initial_delay=retry_delay,
            max_delay=60.0,
            backoff_factor=2.0
        )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Оценивает количество токенов в тексте (грубая аппроксимация).
        
        Args:
            text (str): Текст для оценки
            
        Returns:
            int: Приблизительное количество токенов
        """
        # Простое приближение: ~4 символа на токен для большинства языков
        return len(text) // 4
    
    def can_process_in_one_request(self, messages: List[Dict[str, str]], model: str, max_output_tokens: int = 300) -> bool:
        """
        Проверяет, можно ли обработать сообщения в одном запросе без превышения лимитов контекста.
        
        Args:
            messages (List[Dict[str, str]]): Список сообщений
            model (str): ID модели
            max_output_tokens (int): Максимальное ожидаемое количество токенов в ответе
            
        Returns:
            bool: True, если запрос вписывается в лимиты, иначе False
        """
        # Оценка входящих токенов
        estimated_tokens = sum(self.estimate_tokens(msg["content"]) for msg in messages)
        
        # Получение лимита контекста для модели
        context_limit = 4096  # значение по умолчанию
        
        # Для DeepSeek
        if model == "deepseek-chat":
            context_limit = 4096
        elif model == "deepseek-coder":
            context_limit = 8192
        # Для OpenAI GPT
        elif "gpt-3.5" in model:
            context_limit = 4096
        elif "gpt-4" in model:
            context_limit = 8192
        elif "gpt-4-turbo" in model:
            context_limit = 128000
        
        # Проверка с учетом ожидаемых выходных токенов
        return (estimated_tokens + max_output_tokens) < context_limit
    
    def batch_process_long_context(
        self,
        system_prompt: str,
        user_content: str,
        model: str = "deepseek-chat",
        max_chunk_size: int = 3000,
        overlap: int = 500,
        **kwargs
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Обрабатывает длинный контекст, разбивая его на части и объединяя результаты.
        
        Args:
            system_prompt (str): Системный промпт
            user_content (str): Длинный пользовательский контент
            model (str): ID модели
            max_chunk_size (int): Максимальный размер чанка в символах
            overlap (int): Размер перекрытия между чанками в символах
            **kwargs: Дополнительные параметры для chat_completion
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (объединенный ответ, ошибка)
        """
        # Если текст достаточно короткий, обрабатываем его целиком
        if len(user_content) <= max_chunk_size:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            return self.chat_completion(messages, model=model, **kwargs)
        
        # Разбиваем контент на перекрывающиеся чанки
        chunks = []
        start = 0
        
        while start < len(user_content):
            end = min(start + max_chunk_size, len(user_content))
            
            # Если это не последний чанк, ищем подходящее место для разделения
            if end < len(user_content):
                # Ищем ближайший конец предложения или абзаца
                cutoff = user_content.rfind(". ", start + max_chunk_size - overlap, end)
                if cutoff == -1:
                    cutoff = user_content.rfind("\n", start + max_chunk_size - overlap, end)
                
                if cutoff != -1:
                    end = cutoff + 1  # Включаем точку или перевод строки
            
            chunks.append(user_content[start:end])
            
            # Начинаем следующий чанк с перекрытием
            if end < len(user_content):
                start = max(0, end - overlap)
            else:
                break
        
        # Обрабатываем каждый чанк
        responses = []
        errors = []
        
        for i, chunk in enumerate(chunks):
            # Модифицируем промпт для чанка, указывая его позицию
            chunk_system_prompt = f"{system_prompt}\nЭто часть {i+1} из {len(chunks)} большого текста."
            
            if i > 0:
                chunk_system_prompt += "\nИспользуй результаты предыдущих частей для контекста."
                
            if i < len(chunks) - 1:
                chunk_system_prompt += "\nЭта часть не завершает весь текст."
            
            messages = [
                {"role": "system", "content": chunk_system_prompt}
            ]
            
            # Добавляем результаты предыдущих частей как контекст
            if i > 0 and responses:
                context = "\n".join([f"Результаты части {j+1}: {resp}" for j, resp in enumerate(responses)])
                messages.append({"role": "user", "content": f"Контекст из предыдущих частей:\n{context}\n\nТекущая часть текста:\n{chunk}"})
            else:
                messages.append({"role": "user", "content": chunk})
            
            # Обрабатываем чанк
            response, error = self.chat_completion(messages, model=model, **kwargs)
            
            if response:
                responses.append(response)
            if error:
                errors.append(f"Ошибка в части {i+1}: {error}")
        
        # Если есть хотя бы один успешный ответ
        if responses:
            # Если были ошибки, добавляем информацию о них
            if errors:
                error_summary = "\n".join(errors)
                return "\n\n".join(responses), f"Частичный успех с ошибками: {error_summary}"
            else:
                return "\n\n".join(responses), None
        else:
            # Если все запросы завершились с ошибкой
            return None, "\n".join(errors)
    
    def change_provider(self, api_key: str, base_url: str):
        """
        Изменяет провайдера LLM сервиса.
        
        Args:
            api_key (str): Новый API ключ
            base_url (str): Новый базовый URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.client = OpenAI(api_key=api_key, base_url=base_url)


# Пример использования:
if __name__ == "__main__":

    # Пример для тестирования
    api_key = "your-api-key-here"
    llm_service = LLMServiceProvider(api_key)
    
    messages = [
        {"role": "system", "content": "Вы - полезный ассистент."},
        {"role": "user", "content": "Опиши 3 основных принципа анализа данных."}
    ]
    
    response, error = llm_service.chat_completion(
        messages=messages,
        temperature=0.7,
        max_tokens=300
    )
    
    if response:
        print("Ответ:", response)
    if error:
        print("Ошибка:", error)