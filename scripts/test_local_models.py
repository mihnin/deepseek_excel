#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к локальным моделям
"""

import sys
import os
import requests
import json
from typing import Dict, Tuple

# Добавляем корневую директорию проекта в path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.llm.unified_provider import UnifiedLLM

def test_connection(provider: str, base_url: str) -> Tuple[bool, str]:
    """
    Тестирует подключение к провайдеру
    
    Args:
        provider: Название провайдера
        base_url: Базовый URL
        
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    print(f"\n{'='*50}")
    print(f"Тестирование {provider.upper()}")
    print(f"URL: {base_url}")
    print('='*50)
    
    # Проверяем разные endpoints в зависимости от провайдера
    endpoints_to_test = []
    
    if provider == "ollama":
        endpoints_to_test = [
            (f"{base_url}/api/tags", "GET", "Ollama API (список моделей)"),
            (f"{base_url}/v1/models", "GET", "OpenAI-совместимый endpoint (новое в 2024)")
        ]
    elif provider == "lmstudio":
        endpoints_to_test = [
            (f"{base_url}/models", "GET", "LM Studio API (список моделей)")
        ]
    elif provider == "textgen_webui":
        endpoints_to_test = [
            (f"{base_url}/models", "GET", "Text Gen WebUI API (список моделей)")
        ]
    
    success = False
    message = ""
    
    for endpoint, method, description in endpoints_to_test:
        try:
            print(f"  Проверка: {description}")
            print(f"  Endpoint: {endpoint}")
            
            if method == "GET":
                response = requests.get(endpoint, timeout=5)
            else:
                response = requests.post(endpoint, json={}, timeout=5)
            
            if response.status_code == 200:
                print(f"  OK: Успешно (код {response.status_code})")
                
                # Пытаемся получить список моделей
                try:
                    data = response.json()
                    if provider == "ollama" and "models" in data:
                        models = data["models"]
                        print(f"  OK Найдено моделей: {len(models)}")
                        for model in models[:3]:  # Показываем первые 3
                            print(f"    - {model.get('name', 'unknown')}")
                    elif "data" in data:
                        models = data["data"]
                        print(f"  OK Найдено моделей: {len(models)}")
                        for model in models[:3]:
                            print(f"    - {model.get('id', 'unknown')}")
                except:
                    pass
                    
                success = True
                message = "Подключение успешно"
            else:
                print(f"  ERROR Ошибка (код {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print(f"  ERROR Не удалось подключиться")
            message = f"Сервер {provider} не запущен или недоступен по адресу {base_url}"
        except requests.exceptions.Timeout:
            print(f"  ERROR Таймаут подключения")
            message = "Превышено время ожидания ответа"
        except Exception as e:
            print(f"  ERROR Ошибка: {e}")
            message = str(e)
    
    return success, message

def test_llm_provider(provider_type: str, provider: str, base_url: str, model: str = None):
    """
    Тестирует LLM провайдера через UnifiedLLM
    """
    print(f"\nТестирование через UnifiedLLM...")
    
    config = {
        "provider_type": "local",
        "local_provider": provider,
        "local_base_url": base_url,
        "local_model": model or "test-model"
    }
    
    try:
        llm = UnifiedLLM(config)
        print("OK Провайдер создан")
        
        # Простой тестовый запрос
        test_prompt = "Ответь одним словом: какой сегодня день?"
        
        print(f"Отправка тестового запроса: '{test_prompt}'")
        response, usage = llm.chat_completion(test_prompt, model=model)
        
        if response:
            print(f"OK Получен ответ: {response[:100]}...")
            return True
        else:
            print(f"ERROR Ошибка: {usage}")
            return False
            
    except Exception as e:
        print(f"ERROR Ошибка при создании провайдера: {e}")
        return False

def main():
    """Основная функция"""
    
    print("ТЕСТИРОВАНИЕ ЛОКАЛЬНЫХ МОДЕЛЕЙ")
    print("================================\n")
    
    # Конфигурация провайдеров
    providers = {
        "ollama": {
            "base_url": "http://localhost:11434",
            "test_model": "llama2"
        },
        "lmstudio": {
            "base_url": "http://localhost:1234/v1",
            "test_model": None  # LM Studio сам выберет загруженную модель
        },
        "textgen_webui": {
            "base_url": "http://localhost:5000/v1",
            "test_model": None
        }
    }
    
    results = {}
    
    # Тестируем каждого провайдера
    for provider, config in providers.items():
        success, message = test_connection(provider, config["base_url"])
        results[provider] = {
            "connection": success,
            "message": message
        }
        
        # Если подключение успешно, пробуем отправить запрос
        if success and config.get("test_model"):
            llm_success = test_llm_provider(
                "local", 
                provider, 
                config["base_url"], 
                config["test_model"]
            )
            results[provider]["llm_test"] = llm_success
    
    # Итоговый отчет
    print("\n" + "="*50)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*50)
    
    for provider, result in results.items():
        status = "OK" if result["connection"] else "ERROR"
        print(f"\n{provider.upper()}:")
        print(f"  Подключение: {status}")
        if not result["connection"]:
            print(f"  Сообщение: {result['message']}")
            print(f"  Рекомендация: Запустите {provider} перед использованием")
        elif "llm_test" in result:
            llm_status = "OK" if result["llm_test"] else "ERROR"
            print(f"  LLM тест: {llm_status}")
    
    print("\n" + "="*50)
    print("\nДля запуска провайдеров:")
    print("  Ollama: ollama serve (затем ollama pull llama2)")
    print("  LM Studio: Запустите приложение и нажмите 'Start Server'")
    print("  Text Gen WebUI: python server.py --api")

if __name__ == "__main__":
    main()