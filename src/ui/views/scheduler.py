# ui/scheduler_view.py

import streamlit as st
import os
from src.services.scheduler import TaskScheduler

def render_scheduler_ui():
    """Отображает UI для планировщика задач"""
    st.title("Планировщик задач")
    
    # Инициализация планировщика
    scheduler = TaskScheduler()
    
    # Показать текущие задачи
    st.subheader("Текущие задачи")
    
    tasks = scheduler.tasks
    if not tasks:
        st.info("Нет запланированных задач")
    else:
        for task in tasks:
            with st.expander(f"📅 {task['name']} ({task['schedule_type']} {task['schedule_value']})"):
                st.write(f"Excel-файл: {task['excel_path']}")
                st.write(f"Режим: {task['config'].get('mode', 'Не указан')}")
                st.write(f"Создана: {task['created_at']}")
                st.write(f"Последнее выполнение: {task['last_run'] or 'Нет'}")
                
                if st.button(f"Удалить задачу #{task['id']}", key=f"delete_{task['id']}"):
                    scheduler.remove_task(task['id'])
                    st.success(f"Задача {task['name']} удалена!")
                    st.experimental_rerun()
    
    # Форма для добавления новой задачи
    st.subheader("Добавить новую задачу")
    
    with st.form("new_task_form"):
        task_name = st.text_input("Название задачи")
        
        # Выбор Excel-файла
        excel_files = [f for f in os.listdir() if f.endswith(('.xlsx', '.xls'))]
        excel_path = st.selectbox("Excel-файл", excel_files) if excel_files else st.text_input("Путь к Excel-файлу")
        
        # Режим анализа
        mode = st.selectbox("Режим анализа", ["Построчный анализ", "Анализ всей таблицы", "Комбинированный анализ"])
        
        # Расписание
        schedule_type = st.selectbox("Тип расписания", ["daily", "weekly", "monthly"])
        
        if schedule_type == "daily":
            schedule_value = st.time_input("Время выполнения", value=None)
            schedule_value = schedule_value.strftime("%H:%M") if schedule_value else "12:00"
        elif schedule_type == "weekly":
            day = st.selectbox("День недели", ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
            time = st.time_input("Время", value=None)
            time = time.strftime("%H:%M") if time else "12:00"
            schedule_value = f"{day} {time}"
        elif schedule_type == "monthly":
            day = st.number_input("День месяца", min_value=1, max_value=31, value=1)
            time = st.time_input("Время", value=None)
            time = time.strftime("%H:%M") if time else "12:00"
            schedule_value = f"{day} {time}"
        
        # Дополнительные настройки в зависимости от режима
        config = {
            "mode": mode,
            "llm_settings": {
                "provider_type": "cloud",  # По умолчанию
                "api_key": st.text_input("API ключ", type="password"),
                "model": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 300
            }
        }
        
        if mode in ["Построчный анализ", "Комбинированный анализ"]:
            # Для простоты здесь не реализуем полный интерфейс выбора столбцов,
            # так как это требует загрузки Excel-файла
            config["target_column"] = st.text_input("Целевой столбец")
            
        submitted = st.form_submit_button("Добавить задачу")
        
        if submitted:
            if task_name and excel_path:
                success = scheduler.add_task(task_name, excel_path, config, schedule_type, schedule_value)
                if success:
                    st.success(f"Задача '{task_name}' успешно добавлена!")
                    # Запускаем планировщик, если он еще не запущен
                    if not scheduler.running:
                        scheduler.start()
                    st.experimental_rerun()
            else:
                st.error("Необходимо указать название задачи и путь к Excel-файлу")
    
    # Управление планировщиком
    st.subheader("Управление планировщиком")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Запустить планировщик", disabled=scheduler.running):
            scheduler.start()
            st.success("Планировщик задач запущен!")
    
    with col2:
        if st.button("Остановить планировщик", disabled=not scheduler.running):
            scheduler.stop()
            st.success("Планировщик задач остановлен!")