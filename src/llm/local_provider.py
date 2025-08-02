# local_llm_integration.py
import requests
import json
import time
from typing import Dict, List, Tuple, Optional, Any, Union
import logging

class LocalLLMProvider:
    """
    Класс для работы с локально развернутыми LLM моделями.
    Поддерживает Ollama, LM Studio, Text Generation WebUI и другие.
    """
    
    def __init__(
        self, 
        provider: str = "ollama",
        base_url: str = "http://localhost:11434",
        timeout: int = 60
    ):
        """
        Инициализирует клиент для работы с локальной LLM.
        
        Args:
            provider (str): Тип локального провайдера (ollama, lmstudio, textgen_webui)
            base_url (str): Базовый URL API локальной модели
            timeout (int): Таймаут запросов в секундах
        """
        self.provider = provider.lower()
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger("LocalLLM")
        
        # Проверяем доступность сервиса
        self.is_available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """
        Проверяет доступность локального LLM сервиса.
        
        Returns:
            bool: True если сервис доступен, иначе False
        """
        try:
            if self.provider == "ollama":
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            elif self.provider == "lmstudio":
                # LM Studio URL уже содержит /v1
                response = requests.get(f"{self.base_url}/models", timeout=5)
                return response.status_code == 200
            elif self.provider == "textgen_webui":
                response = requests.get(f"{self.base_url}/v1/models", timeout=5)
                return response.status_code == 200
            else:
                # Для других провайдеров пробуем простой запрос
                response = requests.get(self.base_url, timeout=5)
                return response.status_code < 400
        except Exception as e:
            self.logger.warning(f"Не удалось подключиться к локальной модели: {e}")
            return False
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных локальных моделей.
        
        Returns:
            List[Dict[str, Any]]: Список моделей
        """
        if not self.is_available:
            return []
            
        try:
            if self.provider == "ollama":
                response = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
                if response.status_code == 200:
                    models_data = response.json().get("models", [])
                    return [{"id": model["name"], "name": model["name"]} for model in models_data]
            
            elif self.provider in ["lmstudio", "textgen_webui"]:
                # URL уже содержит /v1 для этих провайдеров
                response = requests.get(f"{self.base_url}/models", timeout=self.timeout)
                if response.status_code == 200:
                    models_data = response.json().get("data", [])
                    return [{"id": model["id"], "name": model["id"]} for model in models_data]
            
            # Если не удалось получить список или неизвестный провайдер
            return [{"id": "local_model", "name": "Локальная модель"}]
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении списка моделей: {e}")
            return [{"id": "local_model", "name": "Локальная модель (fallback)"}]
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2",
        temperature: float = 0.7,
        max_tokens: int = 300,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Выполняет запрос к локальной LLM с механизмом повторных попыток.
        
        Args:
            messages (List[Dict[str, str]]): Список сообщений для отправки
            model (str): Название локальной модели
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
        if not self.is_available:
            return None, "Локальная модель недоступна. Проверьте, запущен ли сервис."
        
        attempt = 0
        last_error = None
        
        while attempt < max_retries:
            attempt += 1
            try:
                # Формирование запроса в зависимости от провайдера
                if self.provider == "ollama":
                    return self._ollama_completion(messages, model, temperature, max_tokens, top_p)
                elif self.provider in ["lmstudio", "textgen_webui"]:
                    return self._openai_compatible_completion(messages, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty)
                else:
                    return None, f"Неподдерживаемый тип локального провайдера: {self.provider}"
                
            except Exception as e:
                last_error = f"Ошибка в попытке {attempt}: {str(e)}"
                
                # Если это последняя попытка, возвращаем ошибку
                if attempt >= max_retries:
                    return None, last_error
                
                # Иначе делаем паузу перед следующей попыткой
                time.sleep(retry_delay)
        
        return None, f"Не удалось получить ответ после {max_retries} попыток"
    
    def _ollama_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Выполняет запрос к Ollama API.
        
        Args:
            messages: Список сообщений
            model: Название модели
            temperature: Температура
            max_tokens: Максимальное количество токенов
            top_p: Top-p параметр
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (ответ, ошибка)
        """
        # Формирование данных запроса для Ollama
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p
            },
            "stream": False
        }
        
        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                return result.get("message", {}).get("content", ""), None
            except Exception as e:
                return None, f"Ошибка при обработке ответа: {e}"
        else:
            return None, f"Ошибка API: {response.status_code} - {response.text}"
    
    def _openai_compatible_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        frequency_penalty: float,
        presence_penalty: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Выполняет запрос к API, совместимому с OpenAI (LM Studio, Text Generation WebUI).
        
        Args:
            messages: Список сообщений
            model: Название модели
            temperature: Температура
            max_tokens: Максимальное количество токенов
            top_p: Top-p параметр
            frequency_penalty: Штраф за частоту
            presence_penalty: Штраф за присутствие
            
        Returns:
            Tuple[Optional[str], Optional[str]]: (ответ, ошибка)
        """
        # Формирование данных запроса для OpenAI-совместимого API
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": False
        }
        
        # URL уже содержит /v1 для lmstudio и textgen_webui
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=self.timeout
        )
        
        if response.status_code == 200:
            try:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", ""), None
            except Exception as e:
                return None, f"Ошибка при обработке ответа: {e}"
        else:
            return None, f"Ошибка API: {response.status_code} - {response.text}"
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Получает информацию о конкретной модели.
        
        Args:
            model_name (str): Название модели
            
        Returns:
            Dict[str, Any]: Информация о модели
        """
        if not self.is_available:
            return {"name": model_name, "status": "unavailable"}
            
        try:
            if self.provider == "ollama":
                # Для Ollama можно получить детальную информацию о модели
                response = requests.post(
                    f"{self.base_url}/api/show",
                    json={"name": model_name},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    model_info = response.json()
                    return {
                        "name": model_name,
                        "parameters": model_info.get("parameters", {}),
                        "template": model_info.get("template", ""),
                        "status": "available"
                    }
            
            # Для других провайдеров просто возвращаем базовую информацию
            return {"name": model_name, "status": "available"}
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении информации о модели: {e}")
            return {"name": model_name, "status": "error", "error": str(e)}
    
    def ping(self) -> bool:
        """
        Проверяет доступность сервиса.
        
        Returns:
            bool: True если сервис доступен, иначе False
        """
        return self._check_availability()

# Класс для объединения локальных и удаленных LLM в едином интерфейсе
class UnifiedLLMProvider:
    """
    Универсальный класс для работы с различными LLM - как локальными, так и облачными.
    Позволяет легко переключаться между разными провайдерами.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Инициализирует универсальный провайдер LLM.
        
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
            "provider_type": "local",  # local или cloud
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
            # Импортируем класс для облачных LLM
            try:
                from llm_integration import LLMServiceProvider
                self.provider = LLMServiceProvider(
                    api_key=self.config["cloud_api_key"],
                    base_url=self.config["cloud_base_url"]
                )
                self.logger.info(f"Инициализирован облачный провайдер: {self.config['cloud_base_url']}")
            except ImportError:
                self.logger.error("Не удалось импортировать LLMServiceProvider. Проверьте наличие модуля llm_integration.py")
                self.provider = None
        else:
            # Используем локальный провайдер
            self.provider = LocalLLMProvider(
                provider=self.config["local_provider"],
                base_url=self.config["local_base_url"]
            )
            self.logger.info(f"Инициализирован локальный провайдер: {self.config['local_provider']}")
    
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


# Пример использования:
if __name__ == "__main__":
    # Пример для тестирования с локальной моделью Ollama
    llm_provider = LocalLLMProvider(
        provider="ollama",
        base_url="http://localhost:11434"
    )
    
    if llm_provider.is_available:
        print("Доступные модели:", llm_provider.get_available_models())
        
        messages = [
            {"role": "system", "content": "Вы - полезный ассистент."},
            {"role": "user", "content": "Опиши 3 основных принципа анализа данных."}
        ]
        
        response, error = llm_provider.chat_completion(
            messages=messages,
            model="llama2",
            temperature=0.7,
            max_tokens=300
        )
        
        if response:
            print("Ответ:", response)
        if error:
            print("Ошибка:", error)
    else:
        print("Локальная модель недоступна. Убедитесь, что Ollama запущен.")
        
    # Пример универсального провайдера
    unified_provider = UnifiedLLMProvider({
        "provider_type": "local",
        "local_provider": "ollama",
        "local_base_url": "http://localhost:11434"
    })
    
    print("Информация о провайдере:", unified_provider.get_provider_info())