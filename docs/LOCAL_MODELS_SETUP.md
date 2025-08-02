# Настройка локальных моделей для DeepSeek Excel

## Поддерживаемые провайдеры

### 1. 🦙 Ollama
**Сайт**: [https://ollama.com/](https://ollama.com/)

#### Установка
1. Скачайте Ollama для вашей ОС
2. Установите и запустите приложение
3. Загрузите модель: `ollama pull llama2` (или другую модель)

#### Конфигурация
- **Порт**: 11434
- **Base URL**: `http://localhost:11434`
- **API endpoints**:
  - Список моделей: `/api/tags`
  - Чат: `/api/chat`
  - Генерация: `/api/generate`
  - OpenAI-совместимость (новое в 2024): `/v1/chat/completions`

#### Рекомендуемые модели
- `llama3` - универсальная модель
- `deepseek-coder` - для анализа кода
- `mistral` - быстрая и эффективная
- `qwen` - хорошо работает с русским языком

#### Команды
```bash
# Запуск сервера (автоматически при старте)
ollama serve

# Загрузка модели
ollama pull llama3

# Список загруженных моделей
ollama list

# Удаление модели
ollama rm model_name
```

---

### 2. 🖥️ LM Studio
**Сайт**: [https://lmstudio.ai/](https://lmstudio.ai/)

#### Установка
1. Скачайте LM Studio с официального сайта
2. Установите приложение
3. Загрузите модели через интерфейс "Discover"

#### Конфигурация
- **Порт**: 1234
- **Base URL**: `http://localhost:1234/v1`
- **API совместимость**: OpenAI API v1

#### Особенности
- Графический интерфейс для управления моделями
- Поддержка GPU ускорения
- Встроенный чат интерфейс
- Детальные настройки параметров генерации

---

### 3. 📝 Text Generation WebUI (Oobabooga)
**GitHub**: [https://github.com/oobabooga/text-generation-webui](https://github.com/oobabooga/text-generation-webui)

#### Установка
```bash
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui
python -m pip install -r requirements.txt
```

#### Конфигурация
- **Порт API**: 5000 (по умолчанию)
- **Порт WebUI**: 7860
- **Base URL**: `http://localhost:5000/v1`

#### Запуск
```bash
# Базовый запуск с API
python server.py --api

# С изменением порта API
python server.py --api --api-port 5001

# Только API без UI
python server.py --api --nowebui

# С аутентификацией
python server.py --api --api-key your-secret-key
```

#### Особенности
- Поддержка множества форматов моделей
- Расширенные настройки генерации
- Поддержка LoRA и других адаптеров
- Веб-интерфейс для тестирования

---

## 🔧 Настройка в DeepSeek Excel

### Через интерфейс
1. Откройте **"Настройки LLM"** в боковой панели
2. Выберите **"Локальная модель"**
3. Выберите провайдера:
   - **Ollama** → URL: `http://localhost:11434`
   - **LM Studio** → URL: `http://localhost:1234/v1`
   - **Text Gen WebUI** → URL: `http://localhost:5000/v1`
4. Нажмите **"Тестировать соединение"**

### Через конфигурацию
Отредактируйте `config/default_config.json`:

```json
{
  "llm": {
    "local": {
      "base_urls": {
        "ollama": "http://localhost:11434",
        "lmstudio": "http://localhost:1234/v1",
        "textgen_webui": "http://localhost:5000/v1",
        "custom": "http://localhost:8000"
      }
    }
  }
}
```

---

## 🚀 Оптимизация производительности

### Общие рекомендации
1. **Выбор модели**:
   - 7B модели - быстрые, подходят для большинства задач
   - 13B модели - баланс качества и скорости
   - 70B+ модели - максимальное качество, требуют мощное железо

2. **Квантизация**:
   - Q4_K_M - оптимальный баланс качества и скорости
   - Q5_K_M - чуть лучше качество, чуть медленнее
   - Q8_0 - почти без потери качества

3. **Параметры генерации**:
   - `temperature`: 0.7 (баланс креативности)
   - `max_tokens`: 500-1000 (для анализа данных)
   - `context_length`: 2048-4096 (зависит от модели)

### GPU ускорение

#### NVIDIA
```bash
# Для Ollama
OLLAMA_NUM_GPU=1 ollama serve

# Для Text Gen WebUI
python server.py --gpu-memory 10 --cpu-memory 16
```

#### AMD (ROCm)
```bash
# Установка ROCm версии Ollama
# Следуйте инструкциям на ollama.com
```

#### Apple Silicon
LM Studio и Ollama автоматически используют Metal для ускорения

---

## 🐛 Решение проблем

### Ошибка подключения

1. **Проверьте, запущен ли сервер**:
   ```bash
   # Ollama
   curl http://localhost:11434/api/tags
   
   # LM Studio
   curl http://localhost:1234/v1/models
   
   # Text Gen WebUI
   curl http://localhost:5000/v1/models
   ```

2. **Проверьте порты**:
   ```bash
   # Windows
   netstat -an | findstr :11434
   
   # Linux/Mac
   lsof -i :11434
   ```

3. **Firewall/Антивирус**:
   - Добавьте исключения для портов
   - Разрешите приложениям сетевой доступ

### Медленная генерация

1. **Уменьшите размер модели** (7B вместо 13B)
2. **Используйте квантизацию** (Q4_K_M)
3. **Уменьшите max_tokens** и context_length
4. **Включите GPU ускорение**
5. **Закройте другие приложения**

### Нехватка памяти

1. **Ollama**:
   ```bash
   # Ограничить использование памяти
   OLLAMA_MAX_LOADED_MODELS=1 ollama serve
   ```

2. **Text Gen WebUI**:
   ```bash
   # Указать лимиты памяти
   python server.py --gpu-memory 6 --cpu-memory 8
   ```

3. **Общие советы**:
   - Используйте модели меньшего размера
   - Применяйте более агрессивную квантизацию
   - Выгружайте модель после использования

---

## 📚 Полезные ресурсы

- [Ollama модели](https://ollama.com/library)
- [LM Studio документация](https://lmstudio.ai/docs)
- [Text Generation WebUI Wiki](https://github.com/oobabooga/text-generation-webui/wiki)
- [Сравнение локальных LLM](https://github.com/eugeneyan/open-llms)
- [Leaderboard открытых моделей](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)