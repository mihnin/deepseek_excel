import streamlit as st
import pandas as pd
import time
from datetime import datetime
import json
import logging
import os

# Настройка страницы должна быть первой командой Streamlit
st.set_page_config(
    page_title="DeepSeek Excel Processor Pro", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Устанавливаем конфигурацию логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# Импорт модулей приложения
from modules.excel_handler import ExcelHandler
from modules.file_utils import FileProcessor
from modules.prompt_library import get_business_prompts, customize_prompt
from ui.llm_settings_view import llm_settings_ui
from utils.profile_manager import ProfileManager
from utils.config_manager import ConfigManager

# Кэширование загрузки Excel-файла
@st.cache_data
def cached_load_excel(file):
    """Кэшированная загрузка Excel файла"""
    excel_handler = ExcelHandler()
    return excel_handler.load_excel(file)

# Кэширование анализа DataFrame
@st.cache_data
def cached_analyze_dataframe(df):
    """Кэшированный анализ DataFrame"""
    excel_handler = ExcelHandler()
    return excel_handler.analyze_dataframe(df)

# Инициализация менеджера профилей
profile_manager = ProfileManager()

# Получение унифицированного LLM провайдера
def get_unified_llm_provider(settings):
    """
    Возвращает унифицированный LLM провайдер.
    
    Args:
        settings: Настройки LLM
        
    Returns:
        Унифицированный LLM провайдер
    """
    try:
        from modules.unified_llm import UnifiedLLMProvider
        # Проверяем наличие и валидность API ключа
        if settings["provider_type"] == "cloud" and not settings.get("api_key"):
            st.error("API ключ не указан для облачного провайдера")
            return None
            
        # Проверяем URL
        base_url = settings.get("cloud_base_url", "https://api.deepseek.com")
        if not base_url.startswith("https://api.deepseek.com"):
            st.warning(f"Базовый URL '{base_url}' может быть неправильным. Рекомендуемое значение: 'https://api.deepseek.com'")
            
        return UnifiedLLMProvider({
            "provider_type": settings["provider_type"],
            "cloud_api_key": settings["api_key"],
            "cloud_base_url": base_url,
            "local_provider": settings["local_provider"],
            "local_base_url": settings["local_base_url"]
        })
    except ImportError as e:
        st.error(f"Ошибка импорта модулей: {e}")
        return None

# Функция для анализа всей таблицы
def analyze_full_table(df, llm_provider, prompt, settings, context_files=None):
    """
    Анализирует таблицу целиком и возвращает обобщенный результат
    
    Args:
        df: DataFrame для анализа
        llm_provider: Провайдер LLM
        prompt: Текст промпта
        settings: Настройки LLM
        context_files: Дополнительные файлы контекста
        
    Returns:
        tuple: (результат, ошибка)
    """
    # Подготовка контекстной информации о таблице используя кэшированный анализ
    stats = cached_analyze_dataframe(df)
    
    # Подготовка дополнительных файлов контекста
    file_processor = FileProcessor()
    context_text = file_processor.prepare_context_for_analysis(context_files) if context_files else ""
    
    # Создание сообщения для LLM
    messages = [
        {"role": "system", "content": "Вы – эксперт по анализу данных и бизнес-аналитике."},
        {"role": "user", "content": f"""
        {prompt}
        
        Структура таблицы:
        - Название: {getattr(df, 'name', 'Таблица данных')}
        - Количество строк: {len(df)}
        - Количество столбцов: {len(df.columns)}
        - Столбцы: {', '.join(df.columns.tolist())}
        
        Информация о столбцах:
        {json.dumps(stats["dtypes"], ensure_ascii=False, indent=2)}
        
        Статистика по пропущенным значениям:
        {json.dumps(stats["missing_percentage"], ensure_ascii=False, indent=2)}
        
        Первые 5 строк таблицы:
        {df.head(5).to_string()}
        
        {context_text}
        
        Проведи тщательный анализ и предоставь детальные, структурированные результаты с выводами и рекомендациями.
        """}
    ]
    
    # Запрос к провайдеру LLM
    model = settings["model"]
    params = {
        "temperature": settings["temperature"],
        "max_tokens": settings["max_tokens"],
        "top_p": settings["top_p"],
        "frequency_penalty": settings["frequency_penalty"],
        "presence_penalty": settings["presence_penalty"]
    }
    
    return llm_provider.chat_completion(
        messages=messages,
        model=model,
        **params
    )

# Основная функция приложения
def main():
    # Инициализация менеджера конфигурации
    config_manager = ConfigManager()
    
    # Использование конфигурации для параметров страницы
    app_title = config_manager.get("app.title", "DeepSeek Excel Processor Pro")
    app_icon = config_manager.get("app.icon", "📊")
    sidebar_state = config_manager.get("app.sidebar_state", "expanded")
    layout = config_manager.get("app.layout", "wide")
    
    # Инициализация состояния сессии
    if "processing" not in st.session_state:
        st.session_state["processing"] = False
    if "logs" not in st.session_state:
        st.session_state["logs"] = []
    if "df" not in st.session_state:
        st.session_state["df"] = None
    if "result_df" not in st.session_state:
        st.session_state["result_df"] = None
    if "table_analysis_result" not in st.session_state:
        st.session_state["table_analysis_result"] = None
    if "config_manager" not in st.session_state:
        st.session_state["config_manager"] = config_manager
    else:
        config_manager = st.session_state["config_manager"]
    
    # Получение параметра активной вкладки из URL (если есть)
    query_params = st.query_params
    active_tab = query_params.get("active_tab", ["tab1"])[0]
    
    # Боковая панель
    with st.sidebar:
        logo_url = config_manager.get("app.logo_url", "https://via.placeholder.com/100x100.png?text=DeepSeek")
        st.image(logo_url, width=100)
        st.title(app_title)
        
        # Режим работы
        mode_options = config_manager.get("app.modes", ["Построчный анализ", "Анализ всей таблицы", "Комбинированный анализ"])
        mode = st.radio("Режим анализа", mode_options, key="mode")
        
        # Управление профилями настроек
        profile_manager.render_ui()
        
        # Настройки LLM
        llm_settings = llm_settings_ui()
        
        st.divider()
        copyright_text = config_manager.get("app.copyright", "© 2025 DeepSeek Excel Processor Pro")
        st.caption(copyright_text)
    
    # Основная область
    st.title(app_title)
    
    # Вкладки для этапов работы - установка индекса активной вкладки
    tab_index = {"tab1": 0, "tab2": 1, "tab3": 2}.get(active_tab, 0)
    tab1, tab2, tab3 = st.tabs(["1. Загрузка данных", "2. Настройка анализа", "3. Результаты"])

    # Set the active tab based on the query parameter
    if tab_index == 1:
        st.query_params["active_tab"] = "tab2"
        st.rerun()
    elif tab_index == 2:
        st.query_params["active_tab"] = "tab3"
        st.rerun()
    
    # ======================== Вкладка 1: Загрузка данных ========================
    with tab1:
        st.header("Загрузка данных")
        
        excel_file = st.file_uploader(
            "Загрузите Excel файл для анализа", 
            type=["xlsx", "xls"],
            help="Поддерживаются файлы формата Excel (.xlsx, .xls)"
        )
        
        if excel_file is not None:
            try:
                # Используем кэшированную загрузку и анализ
                df = cached_load_excel(excel_file)
                st.session_state["df"] = df
                
                # Кэшированный анализ DataFrame
                stats = cached_analyze_dataframe(df)
                
                st.success(f"Файл успешно загружен. Размер: {stats['rows']} строк × {stats['columns']} столбцов")
                
                # Основная информация о файле
                with st.expander("Информация о данных", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Структура данных")
                        st.write(f"Строк: {stats['rows']}")
                        st.write(f"Столбцов: {stats['columns']}")
                        st.write("Типы данных:")
                        st.write(pd.Series(stats["dtypes"]))
                    
                    with col2:
                        st.subheader("Статистика")
                        st.write("Пропущенные значения по столбцам:")
                        st.write(pd.Series(stats["missing_values"]))
                
                # Предварительный просмотр данных
                st.subheader("Предварительный просмотр")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Проверка на проблемы с данными
                if stats["has_issues"]:
                    for issue in stats["issues"]:
                        st.warning(issue)
            
            except Exception as e:
                st.error(f"Ошибка при чтении файла: {e}")
        
        # Загрузка дополнительных файлов для контекста
        st.subheader("Дополнительные файлы контекста")
        context_files = st.file_uploader(
            "Загрузите дополнительные текстовые файлы для контекста анализа (при необходимости)", 
            type=["txt", "csv", "md", "json"], 
            accept_multiple_files=True
        )
        
        if context_files:
            # Используем FileProcessor для обработки файлов
            file_processor = FileProcessor()
            file_summary = file_processor.summarize_files(context_files)
            
            st.success(f"Загружено файлов контекста: {file_summary['count']}")
            for file_info in file_summary["files"]:
                st.info(f"Файл: {file_info['name']} ({file_info['size']} байт) - Тип: {file_info['type']}")
        
        # Кнопка для перехода к следующей вкладке
        if st.session_state["df"] is not None:
            if st.button("Перейти к настройке анализа ➡️"):
                st.query_params["active_tab"] = "tab2"
                st.rerun()
    
    # ======================== Вкладка 2: Настройка анализа ========================
    with tab2:
        if st.session_state["df"] is None:
            st.info("Сначала загрузите Excel файл на предыдущей вкладке")
        else:
            df = st.session_state["df"]
            st.header("Настройка параметров анализа")
            
            # Общие настройки для всех режимов
            st.subheader("Общие настройки")
            
            # Получение библиотеки промптов
            structured_prompts, flat_prompts = get_business_prompts()
            
            # Выбор промпта из библиотеки или собственный
            prompt_source = st.radio(
                "Источник промпта",
                ["Библиотека готовых промптов", "Собственный промпт"],
                horizontal=True
            )
            
            if prompt_source == "Библиотека готовых промптов":
                prompt_categories = list(structured_prompts.keys())
                selected_category = st.selectbox("Категория промптов", prompt_categories)
                
                category_prompts = structured_prompts[selected_category]
                prompt_names = list(category_prompts.keys())
                selected_prompt_name = st.selectbox("Выберите промпт", prompt_names)
                
                selected_prompt = category_prompts[selected_prompt_name]
                st.session_state["custom_prompt"] = selected_prompt
                
                with st.expander("Предпросмотр выбранного промпта"):
                    st.text_area("Текст промпта", selected_prompt, height=100, disabled=True)
            else:
                custom_prompt = st.text_area(
                    "Введите собственный промпт",
                    value=st.session_state.get("custom_prompt", ""),
                    height=150,
                    placeholder="Например: Проведи анализ текста и выяви ключевые тезисы..."
                )
                st.session_state["custom_prompt"] = custom_prompt
            
            # Настройки в зависимости от режима
            if st.session_state["mode"] == "Построчный анализ":
                st.subheader("Настройки построчного анализа")
                
                # Используем ExcelHandler для рекомендаций столбцов
                excel_handler = ExcelHandler()
                
                # Выбор целевого столбца с рекомендациями
                suggested_target_columns = excel_handler.suggest_target_columns(df)
                target_column = st.selectbox(
                    "Целевой столбец для обработки", 
                    df.columns,
                    index=int(df.columns.get_indexer([suggested_target_columns[0]])[0]) if suggested_target_columns else 0,
                    help="Содержимое этого столбца будет отправлено в LLM для анализа"
                )
                
                # Предлагаем дополнительные столбцы для контекста
                suggested_additional_columns = excel_handler.suggest_additional_columns(df, target_column)
                additional_columns = st.multiselect(
                    "Дополнительные столбцы для контекста",
                    [col for col in df.columns if col != target_column],
                    default=suggested_additional_columns[:2] if len(suggested_additional_columns) >= 2 else suggested_additional_columns,
                    help="Данные из этих столбцов будут добавлены для контекста"
                )
                
                # Пример данных из выбранных столбцов
                st.subheader("Пример выбранных данных")
                example_data = df[[target_column] + additional_columns].head(2)
                st.dataframe(example_data, use_container_width=True)
                
                # Предпросмотр промпта с реальными данными
                with st.expander("Предпросмотр промпта с реальными данными"):
                    example_row = df.iloc[0]
                    # Используем модуль промптов для кастомизации
                    context = {
                        "target_column": target_column,
                        "additional_columns": additional_columns,
                        "row_data": {col: example_row[col] for col in [target_column] + additional_columns}
                    }
                    customized_prompt = customize_prompt(st.session_state["custom_prompt"], context)
                    st.text_area("Пример промпта", customized_prompt, height=200, disabled=True)
            
            elif st.session_state["mode"] == "Анализ всей таблицы":
                st.subheader("Настройки анализа всей таблицы")
                
                # Выбор ключевых столбцов для фокуса анализа
                focus_columns = st.multiselect(
                    "Ключевые столбцы для фокуса анализа (опционально)",
                    df.columns,
                    default=[],
                    help="Модель будет уделять особое внимание выбранным столбцам при анализе"
                )
                
                # Предпросмотр промпта для всей таблицы
                with st.expander("Предпросмотр промпта для всей таблицы"):
                    # Используем модуль промптов для кастомизации
                    context = {
                        "focus_columns": focus_columns
                    }
                    customized_prompt = customize_prompt(st.session_state["custom_prompt"], context)
                    st.text_area("Пример промпта", customized_prompt, height=200, disabled=True)
            
            else:  # Комбинированный анализ
                st.subheader("Настройки комбинированного анализа")
                
                # Настройки для построчного анализа
                row_col1, row_col2 = st.columns(2)
                
                with row_col1:
                    st.markdown("**Настройки построчного анализа**")
                    # Используем ExcelHandler для рекомендаций столбцов
                    excel_handler = ExcelHandler()
                    suggested_target_columns = excel_handler.suggest_target_columns(df)
                    
                    target_column = st.selectbox(
                        "Целевой столбец для обработки", 
                        df.columns,
                        index=int(df.columns.get_indexer([suggested_target_columns[0]])[0]) if suggested_target_columns else 0,
                        help="Содержимое этого столбца будет отправлено в LLM для анализа"
                    )
                
                with row_col2:
                    st.markdown("**Дополнительный контекст**")
                    suggested_additional_columns = excel_handler.suggest_additional_columns(df, target_column)
                    
                    additional_columns = st.multiselect(
                        "Дополнительные столбцы для контекста",
                        [col for col in df.columns if col != target_column],
                        default=suggested_additional_columns[:2] if len(suggested_additional_columns) >= 2 else suggested_additional_columns,
                        help="Данные из этих столбцов будут добавлены для контекста"
                    )
                
                # Настройки для анализа всей таблицы
                st.markdown("**Настройки анализа всей таблицы**")
                focus_columns_table = st.multiselect(
                    "Ключевые столбцы для фокуса в анализе всей таблицы",
                    df.columns,
                    default=[target_column] if target_column else [],
                    help="Модель будет уделять особое внимание этим столбцам при анализе всей таблицы"
                )
                
                # Порядок выполнения
                st.markdown("**Порядок выполнения**")
                execution_order = st.radio(
                    "Выберите порядок выполнения",
                    ["Сначала построчный анализ, затем анализ всей таблицы",
                     "Сначала анализ всей таблицы, затем построчный анализ"],
                    help="Порядок выполнения может влиять на качество результатов"
                )
            
            # Кнопка запуска обработки
            st.subheader("Запуск обработки")
            start_col1, start_col2 = st.columns([3, 1])
            
            with start_col1:
                start_processing = st.button(
                    "🚀 Запустить обработку данных", 
                    type="primary",
                    disabled=st.session_state["processing"] or not llm_settings["api_key"] 
                           if llm_settings["provider_type"] == "cloud" else st.session_state["processing"],
                    help="Запустить обработку с выбранными настройками"
                )
            
            with start_col2:
                estimated_time = "3-5 мин" if st.session_state["mode"] == "Анализ всей таблицы" else f"{df.shape[0] // 2 + 1}-{df.shape[0]} мин" 
                st.info(f"Ожидаемое время: {estimated_time}")
            
            if llm_settings["provider_type"] == "cloud" and not llm_settings["api_key"]:
                st.warning("Для запуска обработки с облачной моделью необходимо ввести API ключ в настройках LLM")
            
            # Логика обработки при нажатии кнопки
            if start_processing:
                # Инициализация унифицированного провайдера LLM
                llm_provider = get_unified_llm_provider(llm_settings)
                
                if llm_provider is None:
                    st.error("Не удалось инициализировать LLM-провайдер")
                else:
                    # Проверяем доступность провайдера
                    if not llm_provider.is_available():
                        if llm_settings["provider_type"] == "cloud":
                            st.error("API недоступен. Проверьте API ключ и соединение с интернетом.")
                        else:
                            st.error(f"Локальная модель недоступна. Проверьте, запущен ли {llm_settings['local_provider']}.")
                    else:
                        st.session_state["processing"] = True
                        st.session_state["logs"] = []
                        
                        if st.session_state["mode"] == "Построчный анализ":
                            # Реализация построчного анализа
                            process_row_by_row(df, llm_provider, llm_settings, target_column, additional_columns, context_files)
                            
                        elif st.session_state["mode"] == "Анализ всей таблицы":
                            # Реализация анализа всей таблицы
                            process_full_table(df, llm_provider, llm_settings, focus_columns, context_files)
                            
                        else:  # Комбинированный анализ
                            # Реализация комбинированного анализа
                            process_combined_analysis(df, llm_provider, llm_settings, target_column, additional_columns, focus_columns_table, execution_order, context_files)
    
    # ======================== Вкладка 3: Результаты ========================
    with tab3:
        if st.session_state["result_df"] is None and st.session_state["table_analysis_result"] is None:
            st.info("После обработки данных здесь появятся результаты")
        else:
            st.header("Результаты обработки")
            
            # Отображение результатов построчного анализа, если есть
            if st.session_state["result_df"] is not None:
                df_result = st.session_state["result_df"]
                result_columns = [col for col in df_result.columns if col.endswith("_Обработано")]
                
                if result_columns:
                    st.subheader("Построчный анализ")
                    st.dataframe(df_result, use_container_width=True)
                    
                    # Подготовка Excel для скачивания
                    excel_handler = ExcelHandler()
                    output = excel_handler.save_to_excel(df_result)
                    
                    # Имя файла с датой и временем
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"processed_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📥 Скачать результат Excel",
                        data=output,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            # Отображение результатов анализа всей таблицы, если есть
            if st.session_state["table_analysis_result"] is not None:
                st.subheader("Анализ всей таблицы")
                
                with st.expander("Результаты анализа всей таблицы", expanded=True):
                    table_result = st.session_state["table_analysis_result"]
                    st.markdown(table_result)
                    
                    # Кнопка для скачивания результата в текстовом формате
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"table_analysis_{timestamp}.md"
                    
                    st.download_button(
                        label="📥 Скачать анализ таблицы (MD)",
                        data=table_result.encode("utf-8"),
                        file_name=filename,
                        mime="text/markdown"
                    )
            
            # Скачивание логов (если есть)
            if st.session_state["logs"]:
                st.subheader("Журнал обработки")
                
                with st.expander("Подробные логи обработки", expanded=False):
                    for log_entry in st.session_state["logs"][:5]:  # Показываем только первые 5 логов
                        st.write(f"Строка {log_entry['row_index']}")
                        for att in log_entry["attempts"]:
                            st.write(f"Попытка {att['attempt_number']}")
                            if att.get("error"):
                                st.write(f"Ошибка: {att['error']}")
                            if att.get("parsed_answer"):
                                st.write(f"Ответ: {att['parsed_answer'][:100]}...")
                        st.divider()
                
                # Подготовка текста логов для скачивания
                log_lines = []
                for row_log in st.session_state["logs"]:
                    log_lines.append(f"=== Строка: {row_log['row_index']} ===")
                    for att in row_log["attempts"]:
                        log_lines.append(f"Попытка {att['attempt_number']}")
                        if "messages" in att:
                            log_lines.append(f"Messages: {att['messages']}")
                        if "raw_response" in att:
                            log_lines.append(f"Raw response: {att['raw_response']}")
                        if "parsed_answer" in att:
                            log_lines.append(f"Parsed answer: {att['parsed_answer']}")
                        if "error" in att:
                            log_lines.append(f"Error: {att['error']}")
                    log_lines.append("")
                
                full_text = "\n".join(log_lines)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    label="📥 Скачать полные логи (TXT)",
                    data=full_text.encode("utf-8"),
                    file_name=f"logs_{timestamp}.txt",
                    mime="text/plain"
                )

# Функции для обработки данных
def process_row_by_row(df, llm_provider, llm_settings, target_column, additional_columns, context_files):
    """Обработка данных построчно"""
    st.session_state["table_analysis_result"] = None
    
    # Показываем прогресс-бар
    progress_text = "Выполняется построчный анализ... Это может занять несколько минут."
    my_bar = st.progress(0, text=progress_text)
    
    try:
        # Подготовка DataFrame для результатов
        result_df = df.copy()
        result_col = f"{target_column}_Обработано"
        result_df[result_col] = ""
        
        # Получаем параметры модели из настроек
        model = llm_settings["model"]
        model_params = {
            "temperature": llm_settings["temperature"],
            "max_tokens": llm_settings["max_tokens"],
            "top_p": llm_settings["top_p"],
            "frequency_penalty": llm_settings["frequency_penalty"],
            "presence_penalty": llm_settings["presence_penalty"]
        }
        
        # Подготовка контекста из дополнительных файлов
        file_processor = FileProcessor()
        context_files_processed = file_processor.process_context_files(context_files) if context_files else None
        context_text = file_processor.prepare_context_for_analysis(context_files_processed) if context_files_processed else ""
        
        for i, row in df.iterrows():
            # Обновляем прогресс-бар
            progress = int((i + 1) / len(df) * 100)
            my_bar.progress(progress, text=f"Обрабатывается строка {i+1} из {len(df)}...")
            
            # Подготовка данных для LLM
            text_for_llm = str(row[target_column])
            additional_context_str = ""
            if additional_columns:
                additional_context = [f"{col}: {row[col]}" for col in additional_columns]
                additional_context_str = "\n".join(additional_context)
            
            # Подготовка промпта с использованием модуля prompt_library
            context = {
                "target_column": target_column,
                "additional_columns": additional_columns,
                "row_data": {col: row[col] for col in [target_column] + additional_columns}
            }
            prompt = customize_prompt(st.session_state["custom_prompt"], context)
            
            # Формирование сообщений для LLM
            messages = [
                {"role": "system", "content": "Вы – полезный аналитический ассистент."},
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        f"{context_text}"
                    )
                }
            ]
            
            # Логирование попыток для данной строки
            row_log = {"row_index": i, "attempts": []}
            max_retries = 3
            attempt = 0
            success = False
            llm_answer = ""
            
            while not success and attempt < max_retries:
                attempt += 1
                attempt_log = {
                    "attempt_number": attempt,
                    "messages": messages,
                    "raw_response": None,
                    "parsed_answer": None,
                    "error": None
                }
                
                try:
                    # Запрос к LLM-провайдеру
                    response, error = llm_provider.chat_completion(
                        messages=messages,
                        model=model,
                        **model_params
                    )
                    
                    if error:
                        attempt_log["error"] = error
                    else:
                        attempt_log["raw_response"] = "Success"
                        attempt_log["parsed_answer"] = response
                        llm_answer = response
                        success = True
                
                except Exception as e:
                    attempt_log["error"] = f"Ошибка при вызове LLM: {e}"
                
                # Добавляем лог по данной попытке
                row_log["attempts"].append(attempt_log)
                
                if not success:
                    time.sleep(2)  # Небольшая задержка перед повторной попыткой
            
            # Записываем результат в DataFrame
            if success:
                result_df.at[i, result_col] = llm_answer
            else:
                result_df.at[i, result_col] = f"Не удалось получить ответ после {max_retries} попыток"
            
            st.session_state["logs"].append(row_log)
            time.sleep(0.5)  # Пауза между обработкой строк
        
        # Сохраняем результаты в session_state
        st.session_state["result_df"] = result_df
        
        # Переходим к вкладке с результатами
        st.query_params["active_tab"] = "tab3"
        st.rerun()
    
    except Exception as e:
        st.error(f"Произошла ошибка при выполнении построчного анализа: {e}")
        logging.error(f"Ошибка построчного анализа: {e}", exc_info=True)
    
    finally:
        # Гарантированный сброс флага обработки
        st.session_state["processing"] = False

def process_full_table(df, llm_provider, llm_settings, focus_columns, context_files):
    """Обработка всей таблицы целиком"""
    try:
        with st.spinner("Выполняется анализ всей таблицы... Это может занять несколько минут."):
            # Подготовка параметров для анализа всей таблицы
            table_model_params = llm_settings.copy()
            table_model_params["max_tokens"] = max(1500, llm_settings["max_tokens"])  # Увеличиваем для анализа таблицы
            
            # Подготовка промпта для всей таблицы
            focus_text = ""
            if focus_columns:
                focus_text = f"Обрати особое внимание на следующие столбцы: {', '.join(focus_columns)}"
            
            # Используем модуль промптов для кастомизации
            context = {
                "focus_columns": focus_columns
            }
            full_prompt = customize_prompt(st.session_state["custom_prompt"], context)
            
            # Обработка контекстных файлов, если есть
            file_processor = FileProcessor()
            context_files_processed = file_processor.process_context_files(context_files) if context_files else None
            
            # Вызов функции анализа всей таблицы
            result, error = analyze_full_table(
                df, 
                llm_provider, 
                full_prompt,
                table_model_params,
                context_files_processed
            )
            
            if error:
                st.error(f"Ошибка при анализе всей таблицы: {error}")
                logging.error(f"Ошибка анализа всей таблицы: {error}")
            else:
                # Сохраняем результат анализа всей таблицы
                st.session_state["table_analysis_result"] = result
                st.session_state["result_df"] = df  # Оригинальный DataFrame
                
                # Переходим к вкладке с результатами
                st.query_params["active_tab"] = "tab3"
                st.rerun()
    
    except Exception as e:
        st.error(f"Произошла ошибка при выполнении анализа всей таблицы: {e}")
        logging.error(f"Ошибка анализа всей таблицы: {e}", exc_info=True)
    
    finally:
        # Гарантированный сброс флага обработки
        st.session_state["processing"] = False

def process_combined_analysis(df, llm_provider, llm_settings, target_column, additional_columns, focus_columns_table, execution_order, context_files):
    """Обработка данных комбинированным способом"""
    try:
        # Подготовка DataFrame для результатов
        result_df = df.copy()
        result_col = f"{target_column}_Обработано"
        result_df[result_col] = ""
        
        # Получаем параметры модели из настроек
        model_params = {
            "temperature": llm_settings["temperature"],
            "max_tokens": llm_settings["max_tokens"],
            "top_p": llm_settings["top_p"],
            "frequency_penalty": llm_settings["frequency_penalty"],
            "presence_penalty": llm_settings["presence_penalty"]
        }
        
        # Параметры для анализа всей таблицы (увеличенное max_tokens)
        table_model_params = model_params.copy()
        table_model_params["max_tokens"] = max(1500, model_params["max_tokens"])
        
        # Подготовка контекстных файлов, если есть
        file_processor = FileProcessor()
        context_files_processed = file_processor.process_context_files(context_files) if context_files else None
        
        if execution_order.startswith("Сначала анализ всей таблицы"):
            # 1. Сначала анализ всей таблицы
            with st.spinner("Выполняется анализ всей таблицы... Это может занять несколько минут."):
                # Подготовка промпта для всей таблицы
                context = {
                    "focus_columns": focus_columns_table
                }
                full_prompt = customize_prompt(st.session_state["custom_prompt"], context)
                
                # Вызов функции анализа всей таблицы
                result, error = analyze_full_table(
                    df, 
                    llm_provider, 
                    full_prompt,
                    table_model_params,
                    context_files_processed
                )
                
                if error:
                    st.error(f"Ошибка при анализе всей таблицы: {error}")
                else:
                    # Сохраняем результат анализа всей таблицы
                    st.session_state["table_analysis_result"] = result
            
            # 2. Затем построчный анализ
            progress_text = "Выполняется построчный анализ... Это может занять несколько минут."
            my_bar = st.progress(0, text=progress_text)
            
            # Добавляем результат анализа всей таблицы как контекст для каждой строки
            table_analysis_context = st.session_state["table_analysis_result"]
            
            # Обрезаем контекст, если он слишком длинный
            if table_analysis_context and len(table_analysis_context) > 2000:
                table_analysis_context = table_analysis_context[:2000] + "... [продолжение обрезано]"
            
            for i, row in df.iterrows():
                # Обновляем прогресс-бар
                progress = int((i + 1) / len(df) * 100)
                my_bar.progress(progress, text=f"Обрабатывается строка {i+1} из {len(df)}...")
                
                # Подготовка данных для LLM с учетом результата анализа всей таблицы
                context = {
                    "target_column": target_column,
                    "additional_columns": additional_columns,
                    "row_data": {col: row[col] for col in [target_column] + additional_columns}
                }
                
                prompt = customize_prompt(st.session_state["custom_prompt"], context)
                
                messages = [
                    {"role": "system", "content": "Вы – полезный аналитический ассистент."},
                    {
                        "role": "user",
                        "content": (
                            f"{prompt}\n\n"
                            f"Результат анализа всей таблицы (используй как контекст):\n{table_analysis_context}"
                        )
                    }
                ]
                
                # Запрос к LLM-провайдеру
                response, error = llm_provider.chat_completion(
                    messages=messages,
                    model=llm_settings["model"],
                    **model_params
                )
                
                # Записываем результат в DataFrame
                if error:
                    result_df.at[i, result_col] = f"Ошибка: {error}"
                else:
                    result_df.at[i, result_col] = response
                
                time.sleep(0.5)  # Пауза между обработкой строк
        
        else:
            # 1. Сначала построчный анализ
            progress_text = "Выполняется построчный анализ... Это может занять несколько минут."
            my_bar = st.progress(0, text=progress_text)
            
            for i, row in df.iterrows():
                # Обновляем прогресс-бар
                progress = int((i + 1) / len(df) * 100)
                my_bar.progress(progress, text=f"Обрабатывается строка {i+1} из {len(df)}...")
                
                # Построчный анализ
                context = {
                    "target_column": target_column,
                    "additional_columns": additional_columns,
                    "row_data": {col: row[col] for col in [target_column] + additional_columns}
                }
                
                prompt = customize_prompt(st.session_state["custom_prompt"], context)
                
                messages = [
                    {"role": "system", "content": "Вы – полезный аналитический ассистент."},
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                # Запрос к LLM-провайдеру
                response, error = llm_provider.chat_completion(
                    messages=messages,
                    model=llm_settings["model"],
                    **model_params
                )
                
                # Записываем результат в DataFrame
                if error:
                    result_df.at[i, result_col] = f"Ошибка: {error}"
                else:
                    result_df.at[i, result_col] = response
                
                time.sleep(0.5)  # Пауза между обработкой строк
            
            # 2. Затем анализ всей таблицы с учетом результатов построчного анализа
            with st.spinner("Выполняется анализ всей таблицы... Это может занять несколько минут."):
                # Подготовка промпта для всей таблицы, включающего результаты построчного анализа
                context = {
                    "focus_columns": focus_columns_table
                }
                
                prompt = customize_prompt(st.session_state["custom_prompt"], context)
                
                full_prompt = f"""
                {prompt}
                
                Обрати внимание, что каждая строка уже была проанализирована по отдельности, 
                и результаты находятся в столбце '{result_col}'. 
                Используй эти результаты для формирования общих выводов и закономерностей.
                
                Проведи комплексный анализ данных и предоставь структурированный отчет 
                с ключевыми выводами, закономерностями и рекомендациями.
                """
                
                # Вызов функции анализа всей таблицы с учетом результатов построчного анализа
                result, error = analyze_full_table(
                    result_df,  # Передаем DataFrame с результатами построчного анализа
                    llm_provider, 
                    full_prompt,
                    table_model_params,
                    context_files_processed
                )
                
                if error:
                    st.error(f"Ошибка при анализе всей таблицы: {error}")
                else:
                    # Сохраняем результат анализа всей таблицы
                    st.session_state["table_analysis_result"] = result
        
        # Сохраняем результаты в session_state
        st.session_state["result_df"] = result_df
        
        # Переходим к вкладке с результатами
        st.query_params["active_tab"] = "tab3"
        st.rerun()
    
    except Exception as e:
        st.error(f"Произошла ошибка при выполнении комбинированного анализа: {e}")
        logging.error(f"Ошибка комбинированного анализа: {e}", exc_info=True)
    
    finally:
        # Гарантированный сброс флага обработки
        st.session_state["processing"] = False

# Запуск приложения
if __name__ == "__main__":
    main()