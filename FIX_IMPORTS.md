# Исправление ошибки "No module named 'modules'"

## Проблема
После реорганизации структуры может появляться ошибка при определенных действиях в UI.

## Решение

### Если ошибка появляется при тестировании соединения с LLM:

1. Проверьте файл `src/ui/views/llm_settings.py`
2. Убедитесь, что все импорты обновлены:
   - `from src.llm.cloud_provider import LLMServiceProvider`
   - `from src.llm.local_provider import LocalLLMProvider`

### Если ошибка появляется в других местах:

Запустите поиск старых импортов:
```bash
# Windows PowerShell
Get-ChildItem -Path . -Filter *.py -Recurse | Select-String -Pattern "from modules\.|import modules"

# или Python
python -c "import os, re; [print(f'{root}/{f}: {line}') for root, dirs, files in os.walk('.') for f in files if f.endswith('.py') for i, line in enumerate(open(os.path.join(root, f), 'r', encoding='utf-8').readlines()) if re.search(r'from modules\.|import modules', line)]"
```

## Проверенные импорты

Все основные импорты работают корректно:
- ✅ Core модули (ExcelHandler, FileProcessor, DataProcessor)
- ✅ LLM провайдеры (UnifiedLLM, CloudProvider, LocalProvider)
- ✅ Services (APIUtils, PromptLibrary)
- ✅ Config (Manager, ProfileManager)
- ✅ UI компоненты (LLMSettings)

## Быстрое исправление

Если ошибка продолжает появляться, выполните:

```python
# Временный фикс - добавить путь к sys.path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

Добавьте эти строки в начало app.py после импортов стандартных библиотек.