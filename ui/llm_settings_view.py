# ui/llm_settings_view.py
# Удалены неиспользуемые импорты (оставлены только используемые)
import streamlit as st
from typing import Dict, Any
import traceback
import logging
import os # Добавлен импорт os

# Определяем путь к основному лог-файлу приложения
# Путь относительно текущего файла (ui/llm_settings_view.py) -> .. -> app.log
LOG_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app.log'))


def llm_settings_ui() -> Dict[str, Any]:
    """
    Отображает настройки LLM с поддержкой как облачных, так и локальных моделей в боковой панели.

    Returns:
        Dict[str, Any]: Настройки LLM
    """
    settings: Dict[str, Any] = {} # Инициализируем словарь настроек

    with st.sidebar:
        st.subheader("Настройки LLM")

        # Выбор типа провайдера
        provider_type = st.radio(
            "Тип LLM сервиса",
            ["Облачный API (DeepSeek)", "Локальная модель"],
            index=0 if st.session_state.get("provider_type", "cloud") == "cloud" else 1,
            horizontal=True,
            key="provider_type_radio" # Добавлен ключ, чтобы избежать конфликта с session_state
        )

        # Сохраняем выбранный тип в session_state (если изменился)
        provider_choice = "cloud" if provider_type == "Облачный API (DeepSeek)" else "local"
        if st.session_state.get("provider_type") != provider_choice:
            st.session_state["provider_type"] = provider_choice
            # Сбрасываем список доступных моделей при смене типа
            if "available_models" in st.session_state:
                del st.session_state["available_models"]
            if "available_local_models" in st.session_state:
                del st.session_state["available_local_models"]
            st.rerun() # Перезапускаем для обновления интерфейса

        # Настройки в зависимости от типа провайдера
        if st.session_state.get("provider_type") == "cloud":
            # Настройки облачного API
            st.text_input(
                "DeepSeek API Key",
                type="password",
                key="api_key", # Используем ключ для session_state
                help="Ключ API для доступа к DeepSeek"
            )

            st.text_input(
                "API Base URL",
                key="cloud_base_url", # Используем ключ для session_state
                help="Базовый URL API (по умолчанию DeepSeek)"
            )
            # Устанавливаем значение по умолчанию, если его нет
            if "cloud_base_url" not in st.session_state:
                st.session_state.cloud_base_url = "https://api.deepseek.com"


            # Проверка соединения
            if st.button("Проверить соединение с API"):
                api_key_value = st.session_state.get("api_key")
                base_url_value = st.session_state.get("cloud_base_url")
                if not api_key_value:
                    st.error("Введите API ключ")
                else:
                    try:
                        # Инициализируем провайдер для проверки
                        from modules.llm_integration import LLMServiceProvider
                        llm_service = LLMServiceProvider(api_key=api_key_value, base_url=base_url_value)

                        # Получаем список моделей - это проверит соединение
                        models = llm_service.get_model_list()
                        if models:
                            st.success(f"Соединение установлено. Доступные модели: {', '.join([m['id'] for m in models[:3]])}")
                            st.session_state["available_models"] = models
                        else:
                            st.warning("Соединение установлено, но не удалось получить список моделей")

                    except Exception as e:
                        st.error(f"Ошибка соединения: {e}")
                        # Записываем traceback в лог
                        logging.error(f"Ошибка соединения с API: {e}\n{traceback.format_exc()}")
                        st.info("Подробности ошибки записаны в файл app.log")


        else: # Настройки локальной модели
            local_provider_options = ["Ollama", "LM Studio", "Text Generation WebUI", "Другой"]
            # Определяем индекс по умолчанию
            current_local_provider_key = st.session_state.get("local_provider", "ollama")
            default_index = 0
            provider_mapping_reverse = {
                "ollama": "Ollama",
                "lmstudio": "LM Studio",
                "textgen_webui": "Text Generation WebUI",
                "custom": "Другой"
            }
            if current_local_provider_key in provider_mapping_reverse:
                 try:
                     default_index = local_provider_options.index(provider_mapping_reverse[current_local_provider_key])
                 except ValueError:
                     default_index = 0 # Если сохраненное значение некорректно

            selected_local_provider_name = st.selectbox(
                "Локальный провайдер",
                local_provider_options,
                index=default_index,
                key="local_provider_selectbox" # Ключ для виджета
            )

            # Преобразуем для внутреннего использования и сохраняем, если изменилось
            provider_mapping = {
                "Ollama": "ollama",
                "LM Studio": "lmstudio",
                "Text Generation WebUI": "textgen_webui",
                "Другой": "custom"
            }
            new_local_provider_key = provider_mapping[selected_local_provider_name]
            if st.session_state.get("local_provider") != new_local_provider_key:
                st.session_state["local_provider"] = new_local_provider_key
                # Сбрасываем URL при смене провайдера
                if "local_base_url" in st.session_state:
                    del st.session_state["local_base_url"]
                # Сбрасываем список моделей
                if "available_local_models" in st.session_state:
                    del st.session_state["available_local_models"]
                st.rerun()


            # Базовый URL в зависимости от провайдера
            default_urls = {
                "ollama": "http://localhost:11434",
                "lmstudio": "http://localhost:1234/v1",
                "textgen_webui": "http://localhost:5000/v1",
                "custom": "http://localhost:8000"
            }
            # Устанавливаем URL по умолчанию, если его нет
            if "local_base_url" not in st.session_state:
                 st.session_state.local_base_url = default_urls.get(st.session_state.get("local_provider", "ollama"), "http://localhost:8000")


            st.text_input(
                "URL локального API",
                key="local_base_url", # Используем ключ для session_state
                help="URL API локальной модели"
            )


            # Проверка соединения с локальной моделью
            if st.button("Проверить соединение с локальной моделью"):
                provider_key = st.session_state.get("local_provider")
                base_url_value = st.session_state.get("local_base_url")
                try:                    # Импортируем класс для работы с локальными моделями
                    from modules.local_llm_integration import LocalLLMProvider
                    
                    # Инициализируем провайдер с правильными параметрами
                    local_llm = LocalLLMProvider(
                        provider=provider_key,
                        base_url=base_url_value
                    )

                    if local_llm.is_available:
                        models = local_llm.get_available_models()
                        if models:
                            model_names = [m.get("name", m.get("id", "unknown")) for m in models[:5]] # Безопасное получение имени
                            st.success(f"Соединение установлено. Доступные модели: {', '.join(model_names)}")
                            st.session_state["available_local_models"] = models
                        else:
                            st.warning("Соединение установлено, но не удалось получить список моделей (ответ пуст).")
                    else:
                        # Получаем имя провайдера для сообщения об ошибке
                        local_provider_name = provider_mapping_reverse.get(provider_key, provider_key) # Используем обратный маппинг
                        st.error(f"Локальная модель недоступна по адресу {base_url_value}. Убедитесь, что {local_provider_name} запущен и URL корректен.")


                except Exception as e:
                    st.error(f"Ошибка соединения: {e}")
                    # Записываем traceback в лог
                    logging.error(f"Ошибка соединения с локальной моделью: {e}\n{traceback.format_exc()}")
                    st.info("Подробности ошибки записаны в файл app.log. Проверьте, что сервис запущен и доступен по указанному адресу.")

            # Дополнительная информация
            with st.expander("Как настроить локальную модель"):
                st.markdown("""
                ### Настройка Ollama

                1. Скачайте и установите [Ollama](https://ollama.ai/)
                2. Запустите Ollama
                3. Загрузите модель командой: `ollama pull llama2` (или другую модель)
                4. Убедитесь, что API доступен по адресу `http://localhost:11434`

                ### Настройка LM Studio

                1. Скачайте и установите [LM Studio](https://lmstudio.ai/)
                2. Загрузите модель через интерфейс приложения
                3. Запустите локальный сервер в разделе "Local Server"
                4. Убедитесь, что API доступен по адресу `http://localhost:1234/v1`

                ### Настройка Text Generation WebUI

                1. Установите [Text Generation WebUI](https://github.com/oobabooga/text-generation-webui)
                2. Запустите сервер с параметром `--api`
                3. Убедитесь, что API доступен по адресу `http://localhost:5000/v1`
                """)

        # Общие настройки модели
        st.subheader("Настройки модели")

        # Выбор модели в зависимости от типа провайдера
        if st.session_state.get("provider_type") == "cloud":
            # Используем список моделей из session_state, если он есть
            available_models_data = st.session_state.get("available_models", [{"id": "deepseek-chat", "name": "DeepSeek Chat"}])
            model_options = [m["id"] for m in available_models_data]
            current_model = st.session_state.get("model", model_options[0] if model_options else "deepseek-chat")
            try:
                model_index = model_options.index(current_model) if current_model in model_options else 0
            except ValueError:
                 model_index = 0

            st.selectbox(
                "Выберите модель",
                model_options,
                index=model_index,
                key="model" # Ключ для сохранения в session_state
            )
        else: # Локальная модель
            available_local_models_data = st.session_state.get("available_local_models", [])
            model_options = [m.get("id", "unknown") for m in available_local_models_data] # Безопасное получение id

            # Если список моделей пуст, добавляем варианты по умолчанию
            if not model_options:
                if st.session_state.get("local_provider") == "ollama":
                    model_options = ["llama2", "mistral", "gemma", "vicuna"]
                else:
                    model_options = ["local_model"] # Общий fallback

            current_local_model = st.session_state.get("local_model", model_options[0] if model_options else "local_model")
            try:
                local_model_index = model_options.index(current_local_model) if current_local_model in model_options else 0
            except ValueError:
                 local_model_index = 0

            st.selectbox(
                "Выберите модель",
                model_options,
                index=local_model_index,
                key="local_model" # Ключ для сохранения в session_state
            )

        # Параметры модели (общие для обоих типов)
        col1, col2 = st.columns(2)

        with col1:
            # Используем ключи для всех слайдеров
            st.slider(
                "Temperature", 0.0, 2.0, key="temperature", help="Контролирует креативность ответов",
                # Устанавливаем значение по умолчанию, если его нет
                value=st.session_state.get("temperature", 0.7)
            )
            st.slider(
                "Max Tokens", 100, 4000, step=50, key="max_tokens", help="Максимальное количество токенов в ответе",
                value=st.session_state.get("max_tokens", 300)
            )

        with col2:
            st.slider(
                "Top P", 0.0, 1.0, step=0.05, key="top_p", help="Ограничивает выбор модели наиболее вероятными токенами",
                value=st.session_state.get("top_p", 1.0)
            )
            st.slider(
                "Frequency Penalty", 0.0, 2.0, step=0.1, key="frequency_penalty", help="Штраф за частое использование токенов",
                value=st.session_state.get("frequency_penalty", 0.0)
            )

        # Presence Penalty вынесен за пределы колонок для лучшего отображения
        st.slider(
            "Presence Penalty", 0.0, 2.0, step=0.1, key="presence_penalty", help="Штраф за использование новых токенов",
            value=st.session_state.get("presence_penalty", 0.0)
        )


        # --- Управление логами ---
        st.divider()
        st.subheader("Управление логами")

        # Кнопка для скачивания логов
        try:
            if os.path.exists(LOG_FILE_PATH):
                 with open(LOG_FILE_PATH, "r", encoding='utf-8') as f:
                    log_content = f.read()
                 st.download_button(
                    label="Скачать лог-файл (app.log)",
                    data=log_content,
                    file_name="app.log",
                    mime="text/plain"
                 )
            else:
                st.info("Файл логов app.log еще не создан.")
        except Exception as e:
            st.error(f"Не удалось прочитать лог-файл: {e}")

        # Кнопка для очистки логов
        if st.button("Очистить лог-файл", help="Это действие удалит все записи из файла app.log."):
            try:
                with open(LOG_FILE_PATH, "w", encoding='utf-8') as f:
                    f.write("") # Перезаписываем файл пустым содержимым
                st.success("Лог-файл успешно очищен.")
                st.rerun() # Используем st.rerun() для обновления интерфейса
            except Exception as e:
                st.error(f"Не удалось очистить лог-файл: {e}")

    # Возвращаем собранные настройки из session_state
    # Используем ключи, заданные для виджетов
    settings['provider_type'] = st.session_state.get("provider_type")
    if settings['provider_type'] == 'cloud':
        settings['api_key'] = st.session_state.get("api_key")
        settings['cloud_base_url'] = st.session_state.get("cloud_base_url")
        settings['model'] = st.session_state.get("model")
    else:
        settings['local_provider'] = st.session_state.get("local_provider")
        settings['local_base_url'] = st.session_state.get("local_base_url")
        settings['local_model'] = st.session_state.get("local_model")

    # Получаем значения параметров модели из session_state, используя ключи
    settings['temperature'] = st.session_state.get("temperature", 0.7)
    settings['max_tokens'] = st.session_state.get("max_tokens", 300)
    settings['top_p'] = st.session_state.get("top_p", 1.0)
    settings['frequency_penalty'] = st.session_state.get("frequency_penalty", 0.0)
    settings['presence_penalty'] = st.session_state.get("presence_penalty", 0.0)


    return settings