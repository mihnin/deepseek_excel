import requests
import json
from .llm_integration import LLMIntegrationInterface
from utils.config_manager import ConfigManager

class XInferenceIntegration(LLMIntegrationInterface):
    """
    Интеграция с платформой XInference.
    """
    def __init__(self):
        self.config = ConfigManager().get_config()
        self.xinference_config = self.config.get('xinference', {})
        self.api_endpoint = self.xinference_config.get('api_endpoint', 'http://localhost:9997/v1/chat/completions') # Пример эндпоинта
        self.model_name = self.xinference_config.get('model_name', 'default-model') # Пример модели
        # Добавьте сюда логику для API ключа, если он нужен
        # self.api_key = self.xinference_config.get('api_key')

    def get_available_models(self):
        """
        Получает список доступных моделей от XInference (если API это поддерживает).
        В качестве заглушки возвращает модель из конфига.
        """
        # TODO: Реализовать запрос к API XInference для получения списка моделей, если возможно
        return [self.model_name]

    def generate_response(self, prompt, model=None, temperature=0.7, max_tokens=150):
        """
        Генерирует ответ от модели XInference.
        """
        if not self.api_endpoint:
            raise ValueError("API endpoint for XInference is not configured.")

        current_model = model if model else self.model_name

        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': f'Bearer {self.api_key}' # Раскомментируйте и адаптируйте, если нужна аутентификация
        }

        # Формат payload может отличаться в зависимости от API XInference
        payload = {
            "model": current_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
            # Добавьте другие параметры при необходимости
        }

        try:
            response = requests.post(self.api_endpoint, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # Проверка на ошибки HTTP
            result = response.json()

            # Извлечение ответа - структура может отличаться
            # Пример для OpenAI-совместимого API
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                # Обработка других возможных форматов ответа
                return f"Не удалось извлечь ответ из XInference: {result}"

        except requests.exceptions.RequestException as e:
            # Обработка ошибок сети или API
            print(f"Ошибка при запросе к XInference API: {e}")
            # Можно добавить логирование ошибки: import logging; logging.error(f"XInference API error: {e}")
            raise ConnectionError(f"Не удалось подключиться к XInference API: {e}")
        except json.JSONDecodeError:
            print(f"Ошибка декодирования JSON ответа от XInference: {response.text}")
            raise ValueError("Неверный формат ответа от XInference API.")
        except Exception as e:
            print(f"Непредвиденная ошибка при работе с XInference: {e}")
            raise

    def update_config(self, new_config):
        """Обновляет конфигурацию для XInference."""
        self.xinference_config = new_config.get('xinference', {})
        self.api_endpoint = self.xinference_config.get('api_endpoint', self.api_endpoint)
        self.model_name = self.xinference_config.get('model_name', self.model_name)
        # self.api_key = self.xinference_config.get('api_key', self.api_key)
        print("Конфигурация XInference обновлена.")

# Пример использования (для тестирования)
if __name__ == '__main__':
    # Убедитесь, что у вас есть базовый config/default_config.json
    # или создайте временный для теста
    try:
        xinference_client = XInferenceIntegration()
        # Пример запроса (потребует запущенного сервера XInference)
        # response = xinference_client.generate_response("Привет, как дела?")
        # print(response)
        print("XInferenceIntegration инициализирован.")
        print(f"Endpoint: {xinference_client.api_endpoint}")
        print(f"Model: {xinference_client.model_name}")
        print(f"Available models: {xinference_client.get_available_models()}")

    except Exception as e:
        print(f"Ошибка при инициализации или тесте: {e}")

