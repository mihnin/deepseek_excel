import streamlit as st
import pandas as pd
import time
from datetime import datetime
from io import BytesIO, StringIO
import json
import os
from openai import OpenAI

# Установка страницы и базовой конфигурации
st.set_page_config(
    page_title="DeepSeek Excel Процессор Pro", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Библиотека бизнес-промптов
def get_business_prompts():
    """Возвращает структурированную библиотеку промптов для бизнес-задач"""
    
    prompts = {
        "Общая аналитика": {
            "Краткая саммаризация": "Сделай краткое и информативное резюме следующего текста в 2-3 предложениях, сохраняя ключевые факты и выводы:",
            "Расширенная саммаризация": "Создай структурированное резюме текста объемом 5-7 предложений. Выдели ключевые тезисы, цифры и выводы. Сохрани тон и направленность исходного текста:",
            "Ключевые моменты": "Выдели 3-5 самых важных ключевых моментов из текста в виде маркированного списка:",
            "Бизнес-рекомендации": "На основе этих данных сформулируй 2-3 конкретных бизнес-рекомендации с обоснованием их потенциальной эффективности:",
            "SWOT-анализ": "Проведи краткий SWOT-анализ по данной информации (сильные стороны, слабые стороны, возможности, угрозы):",
            "Извлечение метрик": "Извлеки из текста все числовые показатели, даты и ключевые метрики в структурированном виде. Сгруппируй связанные метрики:",
        },
        
        "Работа с клиентами": {
            "Анализ отзыва": "Проанализируй этот отзыв клиента. Определи общую тональность, ключевые проблемы, уровень удовлетворенности и предложи меры реагирования:",
            "Категоризация обращения": "Определи категорию обращения клиента (жалоба, запрос информации, предложение, благодарность), оцени приоритет (низкий/средний/высокий) и порекомендуй отдел для обработки:",
            "Выявление потребностей": "На основе данного текста клиента выяви его явные и скрытые потребности, болевые точки и ожидания. Предложи подходящие продукты/услуги из стандартного ассортимента:",
            "Улучшение коммуникации": "Перепиши этот текст коммуникации с клиентом, сделав его более дружелюбным, эмпатичным и ориентированным на решение проблемы клиента:",
            "Прогноз оттока": "Оцени риск оттока клиента на основе этой коммуникации по шкале от 1 до 5. Укажи ключевые индикаторы риска и рекомендуемые удерживающие действия:",
        },
        
        "Маркетинг": {
            "Оптимизация текста": "Улучши этот маркетинговый текст, сделав его более убедительным, конкретным и ориентированным на целевую аудиторию. Сохрани ключевые сообщения, но усиль призыв к действию:",
            "Анализ конкурента": "Проанализируй этот текст о конкуренте и выяви их сильные стороны, уникальные преимущества, целевую аудиторию и возможные слабости. Предложи как мы можем дифференцироваться:",
            "SEO-оптимизация": "Переработай этот текст для лучшей SEO-оптимизации. Выдели 3-5 ключевых слов, которые должны быть включены, и перепиши текст с их органичным использованием, сохраняя читаемость:",
            "Адаптация под аудиторию": "Адаптируй этот общий маркетинговый текст для конкретной целевой аудитории: [описание аудитории из доп. столбца]. Сделай акцент на релевантных для этой аудитории преимуществах:",
        },
        
        "Финансы и отчетность": {
            "Анализ финансовых данных": "Проанализируй эти финансовые показатели. Выяви ключевые тренды, отклонения от плана и потенциальные области для оптимизации расходов:",
            "Пояснение к отчету": "Создай лаконичное пояснение к этим финансовым данным для нетехнических руководителей. Объясни значение ключевых показателей и их влияние на бизнес понятным языком:",
            "Прогноз на основе данных": "На основе этих исторических финансовых данных предложи обоснованный прогноз на следующий квартал. Учти сезонность и выявленные тренды:",
        },
        
        "HR и внутренние коммуникации": {
            "Оптимизация вакансии": "Улучши это описание вакансии, сделав его более привлекательным для кандидатов. Чётко опиши требования, обязанности и преимущества работы. Добавь элементы корпоративной культуры:",
            "Анализ резюме": "Проанализируй это резюме на соответствие требованиям позиции. Выдели сильные стороны кандидата, потенциальные области для вопросов на интервью и общую рекомендацию (подходит/не подходит/возможно):",
            "Обратная связь по работе": "Преобразуй эти заметки по работе сотрудника в конструктивную обратную связь. Выдели достижения, области для улучшения и конкретные рекомендации по развитию:",
        },
        
        "Текстовая аналитика по всей таблице": {
            "Общие тренды": "Проанализируй все данные и выяви основные тренды, повторяющиеся темы и ключевые инсайты. Структурируй выводы по категориям актуальности и значимости:",
            "Сегментация данных": "Проанализируй всю таблицу и предложи логичную сегментацию данных по выявленным паттернам. Для каждого сегмента дай краткую характеристику и приблизительный объем:",
            "Аномалии и выбросы": "Исследуй таблицу и выяви аномальные записи, выбросы и нетипичные паттерны. Оцени их значимость и возможное влияние на общие выводы:",
            "Сводный отчет": "Создай структурированный сводный отчет по всей таблице с ключевыми метриками, выводами и рекомендациями. Включи визуальное представление основных результатов:",
        }
    }
    
    # Плоский список для простого выбора в интерфейсе
    flat_prompts = {}
    for category, category_prompts in prompts.items():
        for name, prompt in category_prompts.items():
            flat_prompts[f"{category}: {name}"] = prompt
            
    return prompts, flat_prompts

# Функция для анализа всей таблицы
def analyze_full_table(df, api_key, model, prompt, params, context_files=None):
    """Анализирует таблицу целиком и возвращает обобщенный результат"""
    
    # Подготовка контекстной информации о таблице
    columns_info = {col: {
        "dtype": str(df[col].dtype), 
        "unique_values": len(df[col].unique()),
        "non_null": df[col].count(),
        "null_count": df[col].isna().sum(),
        "sample": df[col].dropna().head(3).tolist()
    } for col in df.columns}
    
    # Статистика по числовым столбцам
    numeric_stats = {}
    if df.select_dtypes(include=['number']).shape[1] > 0:
        numeric_stats = df.describe().to_dict()
    
    # Подготовка дополнительных файлов контекста
    context_text = ""
    if context_files:
        context_text = "Дополнительные контекстные файлы:\n\n"
        for file in context_files:
            try:
                content = file.getvalue().decode('utf-8')
                # Ограничиваем размер для предотвращения превышения токенов
                if len(content) > 5000:
                    content = content[:5000] + "... [содержимое сокращено]"
                context_text += f"--- Файл: {file.name} ---\n{content}\n\n"
            except:
                context_text += f"--- Файл: {file.name} --- [Не удалось прочитать содержимое]\n\n"
    
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
        {json.dumps(columns_info, ensure_ascii=False, indent=2)}
        
        Статистика по числовым данным:
        {json.dumps(numeric_stats, ensure_ascii=False, indent=2)}
        
        Первые 5 строк таблицы:
        {df.head(5).to_string()}
        
        {context_text}
        
        Проведи тщательный анализ и предоставь детальные, структурированные результаты с выводами и рекомендациями.
        """}
    ]
    
    # Запрос к API модели с повторными попытками
    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        attempt += 1
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=params["temperature"],
                max_tokens=params["max_tokens"],
                top_p=params["top_p"],
                frequency_penalty=params["frequency_penalty"],
                presence_penalty=params["presence_penalty"]
            )
            return response.choices[0].message.content, None
        except Exception as e:
            error = f"Ошибка попытки {attempt}: {str(e)}"
            if attempt == max_retries:
                return None, error
            time.sleep(2)  # Пауза перед повторной попыткой
    
    return None, "Не удалось получить ответ после всех попыток"

# Функция для обработки дополнительных файлов
def process_context_files(files):
    """Обрабатывает дополнительные файлы для контекста"""
    if not files:
        return []
    
    processed_files = []
    for file in files:
        file_bytes = BytesIO(file.read())
        file_bytes.name = file.name
        processed_files.append(file_bytes)
        # Возвращаем указатель в начало для последующего чтения
        file.seek(0)
    
    return processed_files

# Функция для сохранения и загрузки профилей
def manage_profiles():
    if "saved_profiles" not in st.session_state:
        st.session_state["saved_profiles"] = {}
    
    profiles = st.session_state["saved_profiles"]
    
    with st.expander("Управление профилями"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Сохранить текущие настройки")
            profile_name = st.text_input("Название профиля", key="new_profile_name")
            
            if st.button("Сохранить профиль"):
                if profile_name:
                    current_settings = {
                        "model": st.session_state.get("model", "deepseek-chat"),
                        "temperature": st.session_state.get("temperature", 0.7),
                        "max_tokens": st.session_state.get("max_tokens", 300),
                        "top_p": st.session_state.get("top_p", 1.0),
                        "frequency_penalty": st.session_state.get("frequency_penalty", 0.0),
                        "presence_penalty": st.session_state.get("presence_penalty", 0.0),
                        "mode": st.session_state.get("mode", "Построчный анализ"),
                        "custom_prompt": st.session_state.get("custom_prompt", "")
                    }
                    profiles[profile_name] = current_settings
                    st.success(f"Профиль '{profile_name}' успешно сохранен!")
                else:
                    st.warning("Введите название профиля")
        
        with col2:
            st.subheader("Загрузить сохраненный профиль")
            profile_options = list(profiles.keys())
            if profile_options:
                selected_profile = st.selectbox("Выберите профиль", profile_options, key="load_profile_select")
                
                if st.button("Загрузить профиль"):
                    settings = profiles[selected_profile]
                    # Загрузка настроек в session_state
                    for key, value in settings.items():
                        st.session_state[key] = value
                    st.success(f"Профиль '{selected_profile}' загружен!")
            else:
                st.info("Нет сохраненных профилей")

# Функция для отображения настроек модели
def show_model_settings():
    with st.expander("Настройки модели DeepSeek", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            model = st.text_input("Модель", value=st.session_state.get("model", "deepseek-chat"), key="model")
            temperature = st.slider("Temperature", 0.0, 2.0, st.session_state.get("temperature", 0.7), 0.1, key="temperature", 
                                  help="Контролирует креативность ответов. Низкое значение дает более предсказуемые ответы, высокое - более творческие.")
            max_tokens = st.slider("Max Tokens", 100, 4000, st.session_state.get("max_tokens", 300), 50, key="max_tokens",
                                 help="Максимальная длина ответа модели. Увеличьте для более детальных ответов.")
        
        with col2:
            top_p = st.slider("Top P", 0.0, 1.0, st.session_state.get("top_p", 1.0), 0.1, key="top_p",
                            help="Контролирует разнообразие. Значение 1.0 рассматривает все варианты, меньшие значения фокусируются на наиболее вероятных.")
            frequency_penalty = st.slider("Frequency Penalty", 0.0, 2.0, st.session_state.get("frequency_penalty", 0.0), 0.1, key="frequency_penalty",
                                        help="Снижает вероятность повторения одних и тех же фраз.")
            presence_penalty = st.slider("Presence Penalty", 0.0, 2.0, st.session_state.get("presence_penalty", 0.0), 0.1, key="presence_penalty",
                                       help="Стимулирует модель говорить о новых темах, а не повторять уже сказанное.")

# Основная функция приложения
def main():
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
    
    # Боковая панель
    with st.sidebar:
        st.image("https://via.placeholder.com/100x100.png?text=DeepSeek", width=100)
        st.title("DeepSeek Excel Pro")
        
        # API ключ
        api_key = st.text_input("DeepSeek API Key", type="password", key="api_key")
        
        # Режим работы
        mode_options = ["Построчный анализ", "Анализ всей таблицы", "Комбинированный анализ"]
        mode = st.radio("Режим анализа", mode_options, key="mode")
        
        # Управление профилями настроек
        manage_profiles()
        
        # Настройки модели
        show_model_settings()
        
        st.divider()
        st.caption("© 2025 DeepSeek Excel Processor Pro")
    
    # Основная область
    st.title("DeepSeek Excel Processor Pro")
    
    # Вкладки для этапов работы
    tab1, tab2, tab3 = st.tabs(["1. Загрузка данных", "2. Настройка анализа", "3. Результаты"])
    
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
                df = pd.read_excel(excel_file)
                st.session_state["df"] = df
                
                st.success(f"Файл успешно загружен. Размер: {df.shape[0]} строк × {df.shape[1]} столбцов")
                
                # Основная информация о файле
                with st.expander("Информация о данных", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Структура данных")
                        st.write(f"Строк: {df.shape[0]}")
                        st.write(f"Столбцов: {df.shape[1]}")
                        st.write("Типы данных:")
                        st.write(df.dtypes)
                    
                    with col2:
                        st.subheader("Статистика")
                        st.write("Пропущенные значения по столбцам:")
                        st.write(df.isna().sum())
                
                # Предварительный просмотр данных
                st.subheader("Предварительный просмотр")
                st.dataframe(df.head(10), use_container_width=True)
                
                # Проверка на проблемы с данными
                warn_cols = []
                for col in df.columns:
                    if df[col].isna().sum() > df.shape[0] * 0.5:  # Более 50% пропусков
                        warn_cols.append(col)
                
                if warn_cols:
                    st.warning(f"Обнаружены столбцы с большим количеством пропусков: {', '.join(warn_cols)}")
            
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
            st.success(f"Загружено файлов контекста: {len(context_files)}")
            for file in context_files:
                st.info(f"Файл: {file.name} ({file.size} байт)")
        
        # Кнопка для перехода к следующей вкладке
        if st.session_state["df"] is not None:
            st.button("Перейти к настройке анализа ➡️", on_click=lambda: st.query_params.update({"active_tab": "tab2"}))
    
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
                
                # Выбор целевого столбца и дополнительных для контекста
                target_column = st.selectbox(
                    "Целевой столбец для обработки", 
                    df.columns,
                    help="Содержимое этого столбца будет отправлено в LLM для анализа"
                )
                
                additional_columns = st.multiselect(
                    "Дополнительные столбцы для контекста",
                    [col for col in df.columns if col != target_column],
                    default=[],
                    help="Данные из этих столбцов будут добавлены для контекста"
                )
                
                # Пример данных из выбранных столбцов
                st.subheader("Пример выбранных данных")
                example_data = df[[target_column] + additional_columns].head(2)
                st.dataframe(example_data, use_container_width=True)
                
                # Предпросмотр промпта с реальными данными
                with st.expander("Предпросмотр промпта с реальными данными"):
                    example_row = df.iloc[0]
                    text_for_llm = str(example_row[target_column])
                    additional_context_str = ""
                    if additional_columns:
                        additional_context = [f"{col}: {example_row[col]}" for col in additional_columns]
                        additional_context_str = "\n".join(additional_context)
                    
                    full_prompt = f"""
                    {st.session_state["custom_prompt"]}
                    
                    Текст целевого столбца: {text_for_llm}
                    
                    Дополнительные данные:
                    {additional_context_str}
                    """
                    st.text_area("Пример промпта", full_prompt, height=200, disabled=True)
            
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
                    full_table_prompt = f"""
                    {st.session_state["custom_prompt"]}
                    
                    Обрати особое внимание на следующие столбцы: {', '.join(focus_columns) if focus_columns else 'Анализируй все столбцы равнозначно'}
                    
                    Проведи тщательный анализ данных и предоставь структурированный отчет с ключевыми выводами и рекомендациями.
                    """
                    st.text_area("Пример промпта", full_table_prompt, height=200, disabled=True)
            
            else:  # Комбинированный анализ
                st.subheader("Настройки комбинированного анализа")
                
                # Настройки для построчного анализа
                row_col1, row_col2 = st.columns(2)
                
                with row_col1:
                    st.markdown("**Настройки построчного анализа**")
                    target_column = st.selectbox(
                        "Целевой столбец для обработки", 
                        df.columns,
                        help="Содержимое этого столбца будет отправлено в LLM для анализа"
                    )
                
                with row_col2:
                    st.markdown("**Дополнительный контекст**")
                    additional_columns = st.multiselect(
                        "Дополнительные столбцы для контекста",
                        [col for col in df.columns if col != target_column],
                        default=[],
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
                    disabled=st.session_state["processing"] or not api_key,
                    help="Запустить обработку с выбранными настройками"
                )
            
            with start_col2:
                estimated_time = "3-5 мин" if st.session_state["mode"] == "Анализ всей таблицы" else f"{df.shape[0] // 2 + 1}-{df.shape[0]} мин" 
                st.info(f"Ожидаемое время: {estimated_time}")
            
            if not api_key:
                st.warning("Для запуска обработки необходимо ввести API ключ DeepSeek в боковой панели")
            
            # Логика обработки при нажатии кнопки
            if start_processing:
                st.session_state["processing"] = True
                st.session_state["logs"].clear()
                
                if st.session_state["mode"] == "Построчный анализ":
                    st.session_state["table_analysis_result"] = None
                    
                    # Показываем прогресс-бар
                    progress_text = "Выполняется построчный анализ... Это может занять несколько минут."
                    my_bar = st.progress(0, text=progress_text)
                    
                    try:
                        # Логика построчного анализа
                        df = st.session_state["df"]
                        result_col = f"{target_column}_Обработано"
                        df[result_col] = ""
                        
                        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                        
                        # Получаем параметры модели из session_state
                        model_params = {
                            "temperature": st.session_state.get("temperature", 0.7),
                            "max_tokens": st.session_state.get("max_tokens", 300),
                            "top_p": st.session_state.get("top_p", 1.0),
                            "frequency_penalty": st.session_state.get("frequency_penalty", 0.0),
                            "presence_penalty": st.session_state.get("presence_penalty", 0.0)
                        }
                        
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
                            
                            messages = [
                                {"role": "system", "content": "Вы – полезный аналитический ассистент."},
                                {
                                    "role": "user",
                                    "content": (
                                        f"{st.session_state['custom_prompt']}\n\n"
                                        f"Текст целевого столбца: {text_for_llm}\n\n"
                                        f"Дополнительные данные:\n{additional_context_str}"
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
                                    response = client.chat.completions.create(
                                        model=st.session_state.get("model", "deepseek-chat"),
                                        messages=messages,
                                        temperature=model_params["temperature"],
                                        max_tokens=model_params["max_tokens"],
                                        top_p=model_params["top_p"],
                                        frequency_penalty=model_params["frequency_penalty"],
                                        presence_penalty=model_params["presence_penalty"],
                                        stream=False
                                    )
                                    attempt_log["raw_response"] = str(response)
                                    
                                    # Получение и обработка ответа от LLM
                                    llm_answer = response.choices[0].message.content.strip()
                                    attempt_log["parsed_answer"] = llm_answer
                                    success = True
                                
                                except Exception as e:
                                    attempt_log["error"] = f"Ошибка при вызове API: {e}"
                                
                                # Добавляем лог по данной попытке
                                row_log["attempts"].append(attempt_log)
                                
                                if not success:
                                    time.sleep(2)  # Небольшая задержка перед повторной попыткой
                            
                            # Записываем результат в DataFrame
                            if success:
                                df.at[i, result_col] = llm_answer
                            else:
                                df.at[i, result_col] = f"Не удалось получить ответ после {max_retries} попыток"
                            
                            st.session_state["logs"].append(row_log)
                            time.sleep(0.5)  # Пауза между обработкой строк
                        
                        # Сохраняем результаты в session_state
                        st.session_state["result_df"] = df
                        
                        # Переходим к вкладке с результатами
                        st.query_params.update({"active_tab": "tab3"})
                    
                    except Exception as e:
                        st.error(f"Произошла ошибка при выполнении построчного анализа: {e}")
                    
                    finally:
                        # Гарантированный сброс флага обработки
                        st.session_state["processing"] = False
                        
                elif st.session_state["mode"] == "Анализ всей таблицы":
                    try:
                        # Логика анализа всей таблицы
                        df = st.session_state["df"]
                        
                        with st.spinner("Выполняется анализ всей таблицы... Это может занять несколько минут."):
                            # Получаем параметры модели из session_state
                            model_params = {
                                "temperature": st.session_state.get("temperature", 0.7),
                                "max_tokens": st.session_state.get("max_tokens", 1500),  # Больше токенов для анализа всей таблицы
                                "top_p": st.session_state.get("top_p", 1.0),
                                "frequency_penalty": st.session_state.get("frequency_penalty", 0.0),
                                "presence_penalty": st.session_state.get("presence_penalty", 0.0)
                            }
                            
                            # Подготовка промпта для всей таблицы
                            focus_text = ""
                            if 'focus_columns' in locals() and focus_columns:
                                focus_text = f"Обрати особое внимание на следующие столбцы: {', '.join(focus_columns)}"
                            
                            full_prompt = f"""
                            {st.session_state['custom_prompt']}
                            
                            {focus_text}
                            
                            Проведи тщательный анализ данных и предоставь структурированный отчет с ключевыми выводами и рекомендациями.
                            """
                            
                            # Обработка контекстных файлов, если есть
                            context_files_processed = process_context_files(context_files) if context_files else None
                            
                            # Вызов функции анализа всей таблицы
                            result, error = analyze_full_table(
                                df, 
                                api_key, 
                                st.session_state.get("model", "deepseek-chat"),
                                full_prompt,
                                model_params,
                                context_files_processed
                            )
                            
                            if error:
                                st.error(f"Ошибка при анализе всей таблицы: {error}")
                            else:
                                # Сохраняем результат анализа всей таблицы
                                st.session_state["table_analysis_result"] = result
                                st.session_state["result_df"] = df  # Оригинальный DataFrame
                                
                                # Переходим к вкладке с результатами
                                st.query_params.update({"active_tab": "tab3"})
                    
                    except Exception as e:
                        st.error(f"Произошла ошибка при выполнении анализа всей таблицы: {e}")
                    
                    finally:
                        # Гарантированный сброс флага обработки
                        st.session_state["processing"] = False
                
                else:  # Комбинированный анализ
                    try:
                        # Логика комбинированного анализа
                        df = st.session_state["df"]
                        result_col = f"{target_column}_Обработано"
                        df[result_col] = ""
                        
                        # Получаем параметры модели из session_state
                        model_params = {
                            "temperature": st.session_state.get("temperature", 0.7),
                            "max_tokens": st.session_state.get("max_tokens", 300),
                            "top_p": st.session_state.get("top_p", 1.0),
                            "frequency_penalty": st.session_state.get("frequency_penalty", 0.0),
                            "presence_penalty": st.session_state.get("presence_penalty", 0.0)
                        }
                        
                        # Параметры для анализа всей таблицы (увеличенное max_tokens)
                        table_model_params = model_params.copy()
                        table_model_params["max_tokens"] = 1500
                        
                        # Подготовка контекстных файлов, если есть
                        context_files_processed = process_context_files(context_files) if context_files else None
                        
                        if execution_order.startswith("Сначала анализ всей таблицы"):
                            # 1. Сначала анализ всей таблицы
                            with st.spinner("Выполняется анализ всей таблицы... Это может занять несколько минут."):
                                # Подготовка промпта для всей таблицы
                                focus_text = ""
                                if focus_columns_table:
                                    focus_text = f"Обрати особое внимание на следующие столбцы: {', '.join(focus_columns_table)}"
                                
                                full_prompt = f"""
                                {st.session_state['custom_prompt']}
                                
                                {focus_text}
                                
                                Проведи тщательный анализ данных и предоставь структурированный отчет с ключевыми выводами и рекомендациями.
                                """
                                
                                # Вызов функции анализа всей таблицы
                                result, error = analyze_full_table(
                                    df, 
                                    api_key, 
                                    st.session_state.get("model", "deepseek-chat"),
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
                            
                            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                            
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
                                text_for_llm = str(row[target_column])
                                additional_context_str = ""
                                if additional_columns:
                                    additional_context = [f"{col}: {row[col]}" for col in additional_columns]
                                    additional_context_str = "\n".join(additional_context)
                                
                                messages = [
                                    {"role": "system", "content": "Вы – полезный аналитический ассистент."},
                                    {
                                        "role": "user",
                                        "content": (
                                            f"{st.session_state['custom_prompt']}\n\n"
                                            f"Текст целевого столбца: {text_for_llm}\n\n"
                                            f"Дополнительные данные:\n{additional_context_str}\n\n"
                                            f"Результат анализа всей таблицы (используй как контекст):\n{table_analysis_context}"
                                        )
                                    }
                                ]
                                
                                # Логирование и обработка аналогично предыдущим режимам...
                                # (часть с обработкой API-запросов и перезапусками при ошибках)
                                
                                max_retries = 3
                                attempt = 0
                                success = False
                                llm_answer = ""
                                
                                while not success and attempt < max_retries:
                                    attempt += 1
                                    
                                    try:
                                        response = client.chat.completions.create(
                                            model=st.session_state.get("model", "deepseek-chat"),
                                            messages=messages,
                                            temperature=model_params["temperature"],
                                            max_tokens=model_params["max_tokens"],
                                            top_p=model_params["top_p"],
                                            frequency_penalty=model_params["frequency_penalty"],
                                            presence_penalty=model_params["presence_penalty"],
                                            stream=False
                                        )
                                        
                                        # Получение и обработка ответа от LLM
                                        llm_answer = response.choices[0].message.content.strip()
                                        success = True
                                    
                                    except Exception as e:
                                        error_msg = f"Ошибка при вызове API (попытка {attempt}): {e}"
                                        
                                        if attempt == max_retries:
                                            llm_answer = f"Не удалось получить ответ после {max_retries} попыток: {error_msg}"
                                        else:
                                            time.sleep(2)  # Пауза перед повторной попыткой
                                
                                # Записываем результат в DataFrame
                                df.at[i, result_col] = llm_answer
                                time.sleep(0.5)  # Пауза между обработкой строк
                        
                        else:
                            # 1. Сначала построчный анализ
                            progress_text = "Выполняется построчный анализ... Это может занять несколько минут."
                            my_bar = st.progress(0, text=progress_text)
                            
                            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                            
                            for i, row in df.iterrows():
                                # Обновляем прогресс-бар
                                progress = int((i + 1) / len(df) * 100)
                                my_bar.progress(progress, text=f"Обрабатывается строка {i+1} из {len(df)}...")
                                
                                # Построчный анализ (аналогично режиму "Построчный анализ")
                                text_for_llm = str(row[target_column])
                                additional_context_str = ""
                                if additional_columns:
                                    additional_context = [f"{col}: {row[col]}" for col in additional_columns]
                                    additional_context_str = "\n".join(additional_context)
                                
                                messages = [
                                    {"role": "system", "content": "Вы – полезный аналитический ассистент."},
                                    {
                                        "role": "user",
                                        "content": (
                                            f"{st.session_state['custom_prompt']}\n\n"
                                            f"Текст целевого столбца: {text_for_llm}\n\n"
                                            f"Дополнительные данные:\n{additional_context_str}"
                                        )
                                    }
                                ]
                                
                                # Логирование и обработка аналогично предыдущим режимам...
                                max_retries = 3
                                attempt = 0
                                success = False
                                llm_answer = ""
                                
                                while not success and attempt < max_retries:
                                    attempt += 1
                                    
                                    try:
                                        response = client.chat.completions.create(
                                            model=st.session_state.get("model", "deepseek-chat"),
                                            messages=messages,
                                            temperature=model_params["temperature"],
                                            max_tokens=model_params["max_tokens"],
                                            top_p=model_params["top_p"],
                                            frequency_penalty=model_params["frequency_penalty"],
                                            presence_penalty=model_params["presence_penalty"],
                                            stream=False
                                        )
                                        
                                        # Получение и обработка ответа от LLM
                                        llm_answer = response.choices[0].message.content.strip()
                                        success = True
                                    
                                    except Exception as e:
                                        error_msg = f"Ошибка при вызове API (попытка {attempt}): {e}"
                                        
                                        if attempt == max_retries:
                                            llm_answer = f"Не удалось получить ответ после {max_retries} попыток: {error_msg}"
                                        else:
                                            time.sleep(2)  # Пауза перед повторной попыткой
                                
                                # Записываем результат в DataFrame
                                df.at[i, result_col] = llm_answer
                                time.sleep(0.5)  # Пауза между обработкой строк
                            
                            # 2. Затем анализ всей таблицы с учетом результатов построчного анализа
                            with st.spinner("Выполняется анализ всей таблицы... Это может занять несколько минут."):
                                # Подготовка промпта для всей таблицы, включающего результаты построчного анализа
                                focus_text = ""
                                if focus_columns_table:
                                    focus_text = f"Обрати особое внимание на следующие столбцы: {', '.join(focus_columns_table)}"
                                
                                full_prompt = f"""
                                {st.session_state['custom_prompt']}
                                
                                {focus_text}
                                
                                Обрати внимание, что каждая строка уже была проанализирована по отдельности, 
                                и результаты находятся в столбце '{result_col}'. 
                                Используй эти результаты для формирования общих выводов и закономерностей.
                                
                                Проведи комплексный анализ данных и предоставь структурированный отчет 
                                с ключевыми выводами, закономерностями и рекомендациями.
                                """
                                
                                # Вызов функции анализа всей таблицы
                                result, error = analyze_full_table(
                                    df, 
                                    api_key, 
                                    st.session_state.get("model", "deepseek-chat"),
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
                        st.session_state["result_df"] = df
                        
                        # Переходим к вкладке с результатами
                        st.query_params.update({"active_tab": "tab3"})
                    
                    except Exception as e:
                        st.error(f"Произошла ошибка при выполнении комбинированного анализа: {e}")
                    
                    finally:
                        # Гарантированный сброс флага обработки
                        st.session_state["processing"] = False
    
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
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        df_result.to_excel(writer, index=False)
                    processed_data = output.getvalue()
                    
                    # Имя файла с датой и временем
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"processed_{timestamp}.xlsx"
                    
                    st.download_button(
                        label="📥 Скачать результат Excel",
                        data=processed_data,
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

if __name__ == "__main__":
    main()