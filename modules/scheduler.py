# modules/scheduler.py

import schedule
import time
import threading
import os
import pandas as pd
from datetime import datetime
import json
import logging

class TaskScheduler:
    def __init__(self, tasks_file="scheduled_tasks.json"):
        """
        Инициализация планировщика задач.
        
        Args:
            tasks_file (str): Путь к файлу с сохраненными задачами
        """
        self.tasks_file = tasks_file
        self.running = False
        self.thread = None
        self.tasks = self._load_tasks()
        self.logger = logging.getLogger("TaskScheduler")
    
    def _load_tasks(self):
        """Загружает сохраненные задачи из файла"""
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Ошибка при загрузке задач: {e}")
                return []
        return []
    
    def _save_tasks(self):
        """Сохраняет текущие задачи в файл"""
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении задач: {e}")
    
    def add_task(self, task_name, excel_path, config, schedule_type, schedule_value):
        """
        Добавляет новую задачу в планировщик.
        
        Args:
            task_name (str): Название задачи
            excel_path (str): Путь к Excel-файлу
            config (dict): Конфигурация анализа
            schedule_type (str): Тип расписания (daily, weekly, monthly)
            schedule_value (str): Значение для расписания
        
        Returns:
            bool: True если задача добавлена успешно
        """
        task = {
            "id": len(self.tasks) + 1,
            "name": task_name,
            "excel_path": excel_path,
            "config": config,
            "schedule_type": schedule_type,
            "schedule_value": schedule_value,
            "created_at": datetime.now().isoformat(),
            "last_run": None
        }
        
        self.tasks.append(task)
        self._save_tasks()
        self._schedule_task(task)
        return True
    
    def remove_task(self, task_id):
        """Удаляет задачу из планировщика"""
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        self._save_tasks()
        # Очищаем все расписания и перепланируем оставшиеся задачи
        schedule.clear()
        for task in self.tasks:
            self._schedule_task(task)
    
    def _schedule_task(self, task):
        """Планирует выполнение задачи по расписанию"""
        if task["schedule_type"] == "daily":
            # Ежедневно в указанное время
            schedule.every().day.at(task["schedule_value"]).do(
                self._run_task, task_id=task["id"]
            )
        elif task["schedule_type"] == "weekly":
            # Еженедельно в указанный день недели
            day, time = task["schedule_value"].split()
            if day == "monday":
                schedule.every().monday.at(time).do(self._run_task, task_id=task["id"])
            elif day == "tuesday":
                schedule.every().tuesday.at(time).do(self._run_task, task_id=task["id"])
            # ... другие дни недели ...
        elif task["schedule_type"] == "monthly":
            # Реализация ежемесячного расписания требует дополнительной логики
            # ...
        
        self.logger.info(f"Задача {task['name']} запланирована на {task['schedule_type']} {task['schedule_value']}")
    
    def _run_task(self, task_id):
        """Выполняет запланированную задачу"""
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        
        try:
            self.logger.info(f"Выполнение задачи {task['name']}")
            
            # Загрузка Excel
            df = pd.read_excel(task["excel_path"])
            
            # Импортируем нужные модули внутри функции для избежания циклических импортов
            from modules.unified_llm import UnifiedLLM as UnifiedLLMProvider
            
            # Инициализация LLM провайдера
            llm_provider = UnifiedLLMProvider(task["config"]["llm_settings"])
            
            # Выполнение анализа в зависимости от режима
            if task["config"]["mode"] == "Построчный анализ":
                from app import process_row_by_row
                result_df = process_row_by_row(
                    df, 
                    llm_provider, 
                    task["config"]["llm_settings"],
                    task["config"]["target_column"],
                    task["config"].get("additional_columns", []),
                    None  # Контекстные файлы пока не поддерживаются
                )
            # ... другие режимы ...
            
            # Сохранение результатов
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"scheduled_results/{task['name']}_{timestamp}.xlsx"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            result_df.to_excel(output_path, index=False)
            
            # Обновление информации о задаче
            task["last_run"] = datetime.now().isoformat()
            self._save_tasks()
            
            self.logger.info(f"Задача {task['name']} выполнена успешно. Результаты сохранены: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении задачи {task['name']}: {e}", exc_info=True)
    
    def start(self):
        """Запускает планировщик в отдельном потоке"""
        if self.running:
            return False
        
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        
        self.thread = threading.Thread(target=run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        
        self.logger.info("Планировщик задач запущен")
        return True
    
    def stop(self):
        """Останавливает планировщик"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.logger.info("Планировщик задач остановлен")