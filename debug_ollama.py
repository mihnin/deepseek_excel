import logging
import sys
from modules.unified_llm_fixed import UnifiedLLM

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout)
    ],
    force=True
)

# Создаем экземпляр UnifiedLLM для локальной модели
llm = UnifiedLLM({
    "provider_type": "local",
    "local_provider": "ollama",
    "local_base_url": "http://localhost:11434"
})

# Проверяем доступность
available = llm.is_available()
print(f"Is Ollama available: {available}")

if available:
    # Получаем список моделей
    models = llm.get_available_models()
    print(f"Available models: {models}")
    
    # Попытка запроса к модели
    messages = [
        {"role": "system", "content": "Вы - полезный ассистент."},
        {"role": "user", "content": "Привет, как дела?"}
    ]
    
    response, error = llm.chat_completion(
        messages=messages,
        model=models[0]["id"] if models else "llama2",
        max_tokens=50
    )
    
    if error:
        print(f"Error: {error}")
    else:
        print(f"Response: {response}") 