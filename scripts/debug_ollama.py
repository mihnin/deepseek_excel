#!/usr/bin/env python3
# scripts/debug_ollama.py

import logging
import sys
import os

# Добавляем корневую директорию проекта в path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.llm.unified_provider import UnifiedLLM

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

def test_ollama():
    """Тестирует соединение с Ollama"""
    print("Тестирование локального Ollama провайдера...")
    
    # Конфигурация для Ollama
    config = {
        "provider_type": "local",
        "local_provider": "ollama",
        "local_base_url": "http://localhost:11434",
        "local_model": "llama2"
    }
    
    try:
        # Создаем провайдера
        llm = UnifiedLLM(config)
        print("✓ Провайдер создан успешно")
        
        # Тестовый запрос
        prompt = "Привет! Ответь одним словом."
        response, usage = llm.chat_completion(prompt, model="llama2")
        
        print(f"✓ Получен ответ: {response}")
        print(f"✓ Использование: {usage}")
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ollama()