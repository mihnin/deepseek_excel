# План реорганизации структуры проекта DeepSeek Excel

## Выявленные проблемы

### 1. Дублированный код
- `modules/unified_llm.py` и `modules/unified_llm_fixed.py` - дубли с небольшими отличиями
- Множественные тестовые классы в одном файле `tests/test_excel_handler.py`

### 2. Неиспользуемые файлы
- `utils/config_utils.py` - пустой файл
- `utils/excel_utils.py` - пустой файл  
- `modules/ui_components.py` - пустой файл

### 3. Неиспользуемые зависимости в requirements.txt
- scikit-learn
- nltk
- pymorphy2
- langdetect
- altair
- seaborn
- streamlit-aggrid
- streamlit-option-menu
- PyPDF2
- extract-msg
- pdfminer.six
- python-pptx
- joblib
- cachetools
- loguru
- toml
- pyyaml

### 4. Проблемы организации
- Смешение бизнес-логики и UI компонентов
- Нечеткое разделение ответственности между модулями

## Новая структура папок

```
deepseek_excel/
├── app.py                        # Главный файл приложения
├── requirements.txt              # Очищенные зависимости
├── CLAUDE.md                     # Инструкции для Claude
├── README.md                     # Документация
├── LICENSE
│
├── src/                          # Исходный код
│   ├── __init__.py
│   ├── core/                    # Ядро приложения
│   │   ├── __init__.py
│   │   ├── excel_handler.py     # Обработка Excel файлов
│   │   ├── data_processor.py    # Обработка данных
│   │   └── file_processor.py    # Обработка файлов (бывший file_utils.py)
│   │
│   ├── llm/                     # LLM интеграции
│   │   ├── __init__.py
│   │   ├── unified_provider.py  # Унифицированный провайдер (объединенный unified_llm_fixed.py)
│   │   ├── cloud_provider.py    # Облачный провайдер (бывший llm_integration.py)
│   │   ├── local_provider.py    # Локальный провайдер (бывший local_llm_integration.py)
│   │   └── xinference_provider.py # XInference провайдер
│   │
│   ├── ui/                      # UI компоненты
│   │   ├── __init__.py
│   │   ├── views/               # Представления
│   │   │   ├── __init__.py
│   │   │   ├── llm_settings.py
│   │   │   ├── export.py
│   │   │   ├── scheduler.py
│   │   │   └── visualization.py
│   │   └── components/          # Компоненты UI
│   │       ├── __init__.py
│   │       └── navigation.py
│   │
│   ├── services/                # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── api_utils.py         # API утилиты
│   │   ├── prompt_library.py    # Библиотека промптов
│   │   ├── scheduler.py         # Планировщик задач
│   │   └── visualization.py     # Визуализация данных
│   │
│   └── config/                  # Конфигурация
│       ├── __init__.py
│       ├── manager.py           # Менеджер конфигурации
│       └── profile_manager.py   # Менеджер профилей
│
├── tests/                       # Тесты
│   ├── __init__.py
│   ├── unit/                    # Юнит-тесты
│   │   ├── __init__.py
│   │   ├── test_excel_handler.py
│   │   ├── test_api_utils.py
│   │   ├── test_prompt_library.py
│   │   └── test_unified_llm.py
│   └── integration/             # Интеграционные тесты
│       └── __init__.py
│
├── assets/                      # Статические ресурсы
│   ├── css/
│   │   └── custom.css
│   └── images/
│       ├── logo.png
│       ├── 1.png
│       └── 2.png
│
├── config/                      # Файлы конфигурации
│   └── default_config.json
│
├── examples/                    # Примеры
│   └── sample_data.xlsx
│
├── docs/                        # Документация
│   └── api/
│       ├── README.md
│       └── llm_integration.md
│
└── scripts/                     # Вспомогательные скрипты
    ├── run_tests.py
    └── debug_ollama.py
```

## План действий по рефакторингу

### Этап 1: Подготовка
1. ✅ Анализ зависимостей и структуры
2. ✅ Выявление дублированного и неиспользуемого кода
3. ✅ Разработка новой структуры

### Этап 2: Очистка (текущий)
1. Удаление пустых/неиспользуемых файлов
2. Удаление дублированного файла `unified_llm.py`
3. Очистка requirements.txt от неиспользуемых библиотек

### Этап 3: Реорганизация
1. Создание новой структуры папок `src/`
2. Перемещение файлов в соответствующие директории
3. Разделение тестов на отдельные файлы

### Этап 4: Рефакторинг кода
1. Обновление всех импортов
2. Переименование модулей для ясности
3. Исправление путей в конфигурациях

### Этап 5: Тестирование
1. Запуск всех тестов
2. Проверка работоспособности приложения
3. Исправление найденных проблем

## Изменения в зависимостях

### Оставить:
- streamlit
- pandas
- numpy
- openpyxl
- openai
- matplotlib
- plotly
- streamlit-extras
- python-docx (версия 0.8.11)
- schedule (используется в scheduler.py)

### Удалить:
- scikit-learn (не используется)
- nltk (не используется)
- pymorphy2 (не используется)
- langdetect (не используется)
- altair (не используется)
- seaborn (не используется)
- streamlit-aggrid (не используется)
- streamlit-option-menu (не используется)
- PyPDF2 (не используется)
- extract-msg (не используется)
- pdfminer.six (не используется)
- python-pptx (не используется)
- joblib (не используется)
- cachetools (не используется)
- loguru (не используется, используется стандартный logging)
- toml (не используется)
- pyyaml (не используется)

## Примечания

- Все изменения будут проводиться поэтапно с сохранением функциональности
- После каждого этапа будет проводиться тестирование
- Резервные копии критических файлов будут созданы перед изменениями