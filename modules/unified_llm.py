# modules/unified_llm.py
import logging
from typing import Dict, List, Tuple, Optional, Any, Union

# Явные импорты классов провайдеров
from modules.local_llm_integration import LocalLLMProvider
from modules.llm_integration import LLMServiceProvider

class UnifiedLLMProvider:
    """
    Универсальный провайдер LLM, объединяющий локальные и облачные модели
    в едином интерфейсе.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует унифицированный LLM провайдер.
        
        Args:
            config (Dict[str, Any], optional): Конфигурация провайдера
                - provider_type: "cloud" или "local"
                - cloud_api_key: API ключ для облачного провайдера
                - cloud_base_url: URL облачного провайдера
                - local_provider: Тип локального провайдера
                - local_base_url: URL локального провайдера
        """
        self.logger = logging.getLogger("UnifiedLLM")
        
        # Значения по умолчанию
        default_config = {
            "provider_type": "cloud",  # local или cloud
            "cloud_api_key": "",
            "cloud_base_url": "https://api.deepseek.com",
            "local_provider": "ollama",
            "local_base_url": "http://localhost:11434"
        }
        
        # Объединяем с переданной конфигурацией
        self.config = {**default_config, **(config or {})}
        
        # Инициализируем нужный провайдер
        self._init_provider()
    
    def _init_provider(self):
        """Инициализирует провайдер на основе конфигурации"""
        if self.config["provider_type"] == "cloud":
            # Используем глобально импортированный класс
            try:
                self.provider = LLMServiceProvider(
                    api_key=self.config["cloud_api_key"],
                    base_url=self.config["cloud_base_url"]
                )
                self.logger.info(f"Инициализирован облачный провайдер: {self.config['cloud_base_url']}")
            except Exception:
                self.logger.error("Не удалось инициализировать LLMServiceProvider")
                self.provider = None
        else:
            # Используем локальный провайдер
            try:
                self.provider = LocalLLMProvider(
                    provider=self.config["local_provider"],
                    base_url=self.config["local_base_url"]
                )
                self.logger.info(f"Инициализирован локальный провайдер: {self.config['local_provider']}")
            except Exception:
                self.logger.error("Не удалось инициализировать LocalLLMProvider")
                self.provider = None
    
    def switch_provider(self, provider_type: str, **kwargs):
        """
        Переключает тип провайдера.
        
        Args:
            provider_type (str): Тип провайдера ("local" или "cloud")
            **kwargs: Дополнительные параметры конфигурации
        """
        self.config["provider_type"] = provider_type
        
        # Обновляем конфигурацию переданными параметрами
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
        
        # Реинициализируем провайдер
        self._init_provider()
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных моделей текущего провайдера.
        
        Returns:
            List[Dict[str, Any]]: Список моделей
        """
        if self.provider is None:
            return []
            
        try:
            if self.config["provider_type"] == "cloud":
                return self.provider.get_model_list()
            else:
                return self.provider.get_available_models()
        except Exception as e:
            self.logger.error(f"Ошибка при получении списка моделей: {e}")
            return []
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 300,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Выполняет запрос к текущему провайдеру LLM.
        
        Args:
            messages (List[Dict[str, str]]): Список сообщений для отправки
            model (str, optional): Название модели
            temperature (float): Параметр температуры
            max_tokens (int): Максимальное количество токенов в ответе
            top_p (float): Параметр top_p
            frequency_penalty (float): Штраф за повторение
            presence_penalty (float): Штраф за наличие
            max_retries (int): Максимальное количество повторных попыток
            retry_delay (int): Задержка между попытками в секундах
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (ответ, ошибка)
        """
        if self.provider is None:
            return None, "Провайдер не инициализирован"
            
        # Если модель не указана, используем дефолтную для текущего провайдера
        if model is None:
            if self.config["provider_type"] == "cloud":
                model = "deepseek-chat"
            else:
                if self.config["local_provider"] == "ollama":
                    model = "llama2"
                else:
                    model = "local_model"
        
        try:
            return self.provider.chat_completion(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении запроса: {e}")
            return None, f"Ошибка провайдера: {str(e)}"
    
    def is_available(self) -> bool:
        """
        Проверяет доступность текущего провайдера.
        
        Returns:
            bool: True если провайдер доступен, иначе False
        """
        if self.provider is None:
            return False
            
        try:
            if self.config["provider_type"] == "cloud":
                # Для облачного провайдера проверяем наличие API ключа
                return bool(self.config["cloud_api_key"])
            else:
                # Для локального провайдера используем метод ping
                return self.provider.ping()
        except Exception:
            return False
    
    def get_provider_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о текущем провайдере.
        
        Returns:
            Dict[str, Any]: Информация о провайдере
        """
        return {
            "type": self.config["provider_type"],
            "provider": self.config["local_provider"] if self.config["provider_type"] == "local" else "cloud",
            "base_url": self.config["local_base_url"] if self.config["provider_type"] == "local" else self.config["cloud_base_url"],
            "available": self.is_available()
        }