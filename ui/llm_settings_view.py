# ui/llm_settings_view.py
import streamlit as st
from typing import Dict, Any

def llm_settings_ui() -> Dict[str, Any]:
    """
    Отображает настройки LLM с поддержкой как облачных, так и локальных моделей в боковой панели.
    
    Returns:
        Dict[str, Any]: Настройки LLM
    """
    with st.sidebar:
        st.subheader("Настройки LLM")
        
        # Выбор типа провайдера
        provider_type = st.radio(
            "Тип LLM сервиса",
            ["Облачный API (DeepSeek)", "Локальная модель"],
            index=0 if st.session_state.get("provider_type", "cloud") == "cloud" else 1,
            horizontal=True
        )
        
        # Сохраняем выбранный тип в session_state
        st.session_state["provider_type"] = "cloud" if provider_type == "Облачный API (DeepSeek)" else "local"
        
        # Настройки в зависимости от типа провайдера
        if st.session_state["provider_type"] == "cloud":
            # Настройки облачного API
            api_key = st.text_input(
                "DeepSeek API Key", 
                type="password",
                value=st.session_state.get("api_key", ""),
                help="Ключ API для доступа к DeepSeek"
            )
            st.session_state["api_key"] = api_key
            
            base_url = st.text_input(
                "API Base URL",
                value=st.session_state.get("cloud_base_url", "https://api.deepseek.com"),
                help="Базовый URL API (по умолчанию DeepSeek)"
            )
            st.session_state["cloud_base_url"] = base_url
            
            # Проверка соединения
            if st.button("Проверить соединение с API"):
                if not api_key:
                    st.error("Введите API ключ")
                else:
                    try:
                        # Инициализируем провайдер для проверки
                        from modules.llm_integration import LLMServiceProvider
                        llm_service = LLMServiceProvider(api_key=api_key, base_url=base_url)
                        
                        # Получаем список моделей - это проверит соединение
                        models = llm_service.get_model_list()
                        if models:
                            st.success(f"Соединение установлено. Доступные модели: {', '.join([m['id'] for m in models[:3]])}")
                            st.session_state["available_models"] = models
                        else:
                            st.warning("Соединение установлено, но не удалось получить список моделей")
                    
                    except Exception as e:
                        st.error(f"Ошибка соединения: {e}")
        
        else:
            # Настройки локальной модели
            local_provider = st.selectbox(
                "Локальный провайдер",
                ["Ollama", "LM Studio", "Text Generation WebUI", "Другой"],
                index=0 if st.session_state.get("local_provider", "ollama") == "ollama" else 
                     1 if st.session_state.get("local_provider") == "lmstudio" else
                     2 if st.session_state.get("local_provider") == "textgen_webui" else 3
            )
            
            # Преобразуем для внутреннего использования
            provider_mapping = {
                "Ollama": "ollama",
                "LM Studio": "lmstudio",
                "Text Generation WebUI": "textgen_webui",
                "Другой": "custom"
            }
            st.session_state["local_provider"] = provider_mapping[local_provider]
            
            # Базовый URL в зависимости от провайдера
            default_urls = {
                "ollama": "http://localhost:11434",
                "lmstudio": "http://localhost:1234/v1",
                "textgen_webui": "http://localhost:5000/v1",
                "custom": "http://localhost:8000"
            }
            
            local_base_url = st.text_input(
                "URL локального API",
                value=st.session_state.get("local_base_url", default_urls[st.session_state["local_provider"]]),
                help="URL API локальной модели"
            )
            st.session_state["local_base_url"] = local_base_url
            
            # Проверка соединения с локальной моделью
            if st.button("Проверить соединение с локальной моделью"):
                try:
                    # Импортируем класс для работы с локальными моделями
                    from modules.local_llm import LocalLLMProvider
                    
                    local_llm = LocalLLMProvider(
                        provider=st.session_state["local_provider"],
                        base_url=local_base_url
                    )
                    
                    if local_llm.is_available:
                        models = local_llm.get_available_models()
                        if models:
                            model_names = [m["name"] for m in models[:5]]
                            st.success(f"Соединение установлено. Доступные модели: {', '.join(model_names)}")
                            st.session_state["available_local_models"] = models
                        else:
                            st.warning("Соединение установлено, но не удалось получить список моделей")
                    else:
                        st.error(f"Локальная модель недоступна. Убедитесь, что {local_provider} запущен")
                    
                except Exception as e:
                    st.error(f"Ошибка соединения: {e}")
                    st.info("Проверьте, что сервис запущен и доступен по указанному адресу")
            
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
        if st.session_state["provider_type"] == "cloud":
            available_models = st.session_state.get("available_models", [{"id": "deepseek-chat", "name": "DeepSeek Chat"}])
            model_options = [m["id"] for m in available_models]
            
            selected_model = st.selectbox(
                "Выберите модель",
                model_options,
                index=0 if "model" not in st.session_state else 
                    model_options.index(st.session_state["model"]) if st.session_state["model"] in model_options else 0
            )
        else:
            available_models = st.session_state.get("available_local_models", [{"id": "llama2", "name": "Llama 2"}])
            model_options = [m["id"] for m in available_models]
            
            # Если список моделей пуст, добавляем варианты по умолчанию в зависимости от провайдера
            if not model_options:
                if st.session_state["local_provider"] == "ollama":
                    model_options = ["llama2", "mistral", "gemma", "vicuna"]
                else:
                    model_options = ["local_model"]
            
            selected_model = st.selectbox(
                "Выберите модель",
                model_options,
                index=0 if "local_model" not in st.session_state else 
                    model_options.index(st.session_state["local_model"]) if st.session_state["local_model"] in model_options else 0
            )
        
        # Сохраняем выбранную модель
        if st.session_state["provider_type"] == "cloud":
            st.session_state["model"] = selected_model
        else:
            st.session_state["local_model"] = selected_model
        
        # Параметры модели (общие для обоих типов)
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Temperature", 
                0.0, 2.0, 
                st.session_state.get("temperature", 0.7), 
                0.1,
                help="Контролирует креативность ответов"
            )
            st.session_state["temperature"] = temperature
            
            max_tokens = st.slider(
                "Max Tokens", 
                100, 4000, 
                st.session_state.get("max_tokens", 300), 
                50,
                help="Максимальная длина ответа"
            )
            st.session_state["max_tokens"] = max_tokens
        
        with col2:
            top_p = st.slider(
                "Top P", 
                0.0, 1.0, 
                st.session_state.get("top_p", 1.0), 
                0.1,
                help="Вероятностное ограничение"
            )
            st.session_state["top_p"] = top_p
            
            frequency_penalty = st.slider(
                "Frequency Penalty", 
                0.0, 2.0, 
                st.session_state.get("frequency_penalty", 0.0), 
                0.1,
                help="Снижает повторения"
            )
            st.session_state["frequency_penalty"] = frequency_penalty
        
        presence_penalty = st.slider(
            "Presence Penalty", 
            0.0, 2.0, 
            st.session_state.get("presence_penalty", 0.0), 
            0.1,
            help="Поощряет разнообразие"
        )
        st.session_state["presence_penalty"] = presence_penalty
    
    return {
        "provider_type": st.session_state["provider_type"],
        "model": st.session_state["model"] if st.session_state["provider_type"] == "cloud" else st.session_state["local_model"],
        "temperature": st.session_state["temperature"],
        "max_tokens": st.session_state["max_tokens"],
        "top_p": st.session_state["top_p"],
        "frequency_penalty": st.session_state["frequency_penalty"],
        "presence_penalty": st.session_state["presence_penalty"],
        "api_key": st.session_state.get("api_key", ""),
        "cloud_base_url": st.session_state.get("cloud_base_url", "https://api.deepseek.com"),
        "local_provider": st.session_state.get("local_provider", "ollama"),
        "local_base_url": st.session_state.get("local_base_url", "http://localhost:11434")
    }