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