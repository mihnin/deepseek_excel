<!-- docs/api/llm_integration.md -->
# LLM Integration API

The LLM integration API provides interfaces for working with both cloud-based and local language models.

## UnifiedLLMProvider

`UnifiedLLMProvider` is the main class for working with language models. It provides a unified interface for both cloud-based and local models.

### Initialization

```python
provider = UnifiedLLMProvider(config={
    "provider_type": "cloud",  # or "local"
    "cloud_api_key": "your-api-key",
    "cloud_base_url": "https://api.deepseek.com",
    "local_provider": "ollama",
    "local_base_url": "http://localhost:11434"
})

Methods
chat_completion
Sends a request to the LLM and returns the response.
response, error = provider.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=300
)

Parameters:

messages (List[Dict[str, str]]): List of messages to send
model (str, optional): Model name
temperature (float): Temperature parameter
max_tokens (int): Maximum number of tokens in the response
top_p (float): Top-p parameter
frequency_penalty (float): Frequency penalty
presence_penalty (float): Presence penalty
max_retries (int): Maximum number of retries
initial_retry_delay (int): Initial delay between retries in seconds

Returns:

Tuple[Optional[str], Optional[str]]: (response, error)

## Шаг 7: Улучшение модульности и тестируемости

### 7.1. Создание вспомогательного модуля для работы с API

```python
# modules/api_utils.py
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable, TypeVar

T = TypeVar('T')  # Определяем обобщенный тип для функции

class APIUtils:
    """Утилиты для работы с API"""
    
    @staticmethod
    def retry_with_backoff(
        func: Callable[..., Tuple[Optional[T], Optional[str]]],
        *args: Any,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        **kwargs: Any
    ) -> Tuple[Optional[T], Optional[str]]:
        """
        Выполняет функцию с повторными попытками и экспоненциальной задержкой.
        
        Args:
            func: Функция для выполнения, которая возвращает (результат, ошибка)
            *args: Аргументы для функции
            max_retries: Максимальное количество попыток
            initial_delay: Начальная задержка между попытками в секундах
            max_delay: Максимальная задержка между попытками в секундах
            backoff_factor: Множитель для экспоненциальной задержки
            **kwargs: Именованные аргументы для функции
            
        Returns:
            Tuple[Optional[T], Optional[str]]: (результат, ошибка)
        """
        logger = logging.getLogger("APIUtils")
        
        delay = initial_delay
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                result, error = func(*args, **kwargs)
                
                if error is None:
                    return result, None
                
                last_error = error
                
            except Exception as e:
                last_error = f"Исключение в попытке {attempt}: {str(e)}"
                logger.warning(last_error)
            
            # Если это последняя попытка, возвращаем ошибку
            if attempt >= max_retries:
                return None, f"Не удалось выполнить после {max_retries} попыток. Последняя ошибка: {last_error}"
            
            # Иначе делаем паузу и повторяем
            logger.info(f"Попытка {attempt} не удалась. Повторная попытка через {delay:.1f} сек.")
            time.sleep(delay)
            
            # Увеличиваем задержку для следующей попытки, но не более max_delay
            delay = min(delay * backoff_factor, max_delay)
        
        # Этот код не должен выполниться, но для полноты возвращаем ошибку
        return None, f"Не удалось выполнить после {max_retries} попыток."