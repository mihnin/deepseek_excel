# data_processor.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
import re
import io
from datetime import datetime

class DataProcessor:
    """
    Класс для предварительной обработки и анализа данных Excel и текстовых файлов.
    Обеспечивает функции очистки, трансформации и подготовки данных для LLM-анализа.
    """
    
    def __init__(self):
        """Инициализация процессора данных."""
        pass
    
    @staticmethod
    def read_excel(file) -> pd.DataFrame:
        """
        Читает Excel файл и возвращает DataFrame.
        
        Args:
            file: Файл Excel (BytesIO или путь)
            
        Returns:
            pd.DataFrame: Данные из Excel
        """
        try:
            return pd.read_excel(file)
        except Exception as e:
            raise ValueError(f"Ошибка при чтении Excel файла: {e}")
    
    @staticmethod
    def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Анализирует DataFrame и возвращает статистику и метаданные.
        
        Args:
            df (pd.DataFrame): DataFrame для анализа
            
        Returns:
            Dict[str, Any]: Статистика и метаданные
        """
        stats = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
            "missing_percentage": {col: round(df[col].isna().sum() / len(df) * 100, 2) for col in df.columns},
            "unique_values": {col: int(df[col].nunique()) for col in df.columns},
            "sample_values": {col: df[col].dropna().head(3).tolist() for col in df.columns},
            "numeric_columns": list(df.select_dtypes(include=['number']).columns),
            "text_columns": list(df.select_dtypes(include=['object']).columns),
            "date_columns": list(df.select_dtypes(include=['datetime']).columns),
        }
        
        # Добавляем базовую статистику для числовых столбцов
        if stats["numeric_columns"]:
            numeric_stats = df[stats["numeric_columns"]].describe().to_dict()
            stats["numeric_stats"] = numeric_stats
        
        # Анализ текстовых данных
        text_stats = {}
        for col in stats["text_columns"]:
            if df[col].notna().any():
                text_stats[col] = {
                    "avg_length": df[col].astype(str).str.len().mean(),
                    "max_length": df[col].astype(str).str.len().max(),
                    "min_length": df[col].astype(str).str.len().min(),
                }
        stats["text_stats"] = text_stats
        
        return stats
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame, options: Dict[str, bool] = None) -> pd.DataFrame:
        """
        Очищает DataFrame от проблемных данных.
        
        Args:
            df (pd.DataFrame): DataFrame для очистки
            options (Dict[str, bool], optional): Опции очистки
                - remove_duplicates: Удалять дубликаты
                - fill_na: Заполнять пропущенные значения
                - normalize_text: Нормализовать текстовые данные
            
        Returns:
            pd.DataFrame: Очищенный DataFrame
        """
        if options is None:
            options = {
                "remove_duplicates": True,
                "fill_na": True,
                "normalize_text": True
            }
        
        # Создаем копию, чтобы не модифицировать оригинал
        cleaned_df = df.copy()
        
        # Удаление дубликатов
        if options.get("remove_duplicates", True):
            cleaned_df = cleaned_df.drop_duplicates()
        
        # Заполнение пропущенных значений
        if options.get("fill_na", True):
            # Для числовых столбцов используем медиану
            for col in cleaned_df.select_dtypes(include=['number']).columns:
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
            
            # Для текстовых столбцов используем пустую строку
            for col in cleaned_df.select_dtypes(include=['object']).columns:
                cleaned_df[col] = cleaned_df[col].fillna('')
            
            # Для дат используем самую частую дату или текущую
            for col in cleaned_df.select_dtypes(include=['datetime']).columns:
                if cleaned_df[col].notna().any():
                    most_common = cleaned_df[col].mode()[0]
                    cleaned_df[col] = cleaned_df[col].fillna(most_common)
                else:
                    cleaned_df[col] = cleaned_df[col].fillna(pd.Timestamp.now())
        
        # Нормализация текстовых данных
        if options.get("normalize_text", True):
            for col in cleaned_df.select_dtypes(include=['object']).columns:
                # Удаление лишних пробелов
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                # Приведение к нижнему регистру для улучшения поиска
                cleaned_df[col] = cleaned_df[col].str.lower()
        
        return cleaned_df
    
    @staticmethod
    def detect_text_language(text: str) -> str:
        """
        Определяет язык текста (упрощенная версия).
        
        Args:
            text (str): Текст для анализа
            
        Returns:
            str: Код языка (ru, en, etc.)
        """
        # Простая эвристика по наличию кириллических символов
        if re.search('[а-яА-Я]', text):
            return 'ru'
        else:
            return 'en'
    
    @staticmethod
    def extract_key_columns(df: pd.DataFrame, threshold: float = 0.8) -> List[str]:
        """
        Выявляет ключевые столбцы с высоким содержанием уникальных значений.
        
        Args:
            df (pd.DataFrame): DataFrame для анализа
            threshold (float): Пороговое значение уникальности (0-1)
            
        Returns:
            List[str]: Список ключевых столбцов
        """
        key_columns = []
        
        for col in df.columns:
            # Для текстовых столбцов с большим количеством значений
            if df[col].dtype == 'object' and df[col].notna().any():
                unique_ratio = df[col].nunique() / df[col].count()
                if unique_ratio >= threshold:
                    key_columns.append(col)
        
        return key_columns
    
    @staticmethod
    def suggest_column_groups(df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Предлагает логическое группирование столбцов.
        
        Args:
            df (pd.DataFrame): DataFrame для анализа
            
        Returns:
            Dict[str, List[str]]: Группы столбцов
        """
        groups = {
            "ID_columns": [],
            "Name_columns": [],
            "Date_columns": [],
            "Numeric_columns": [],
            "Text_columns": [],
            "Category_columns": []
        }
        
        for col in df.columns:
            # Определение ID-столбцов
            if "id" in col.lower() or "код" in col.lower():
                groups["ID_columns"].append(col)
            
            # Определение столбцов с именами
            elif "name" in col.lower() or "имя" in col.lower() or "название" in col.lower():
                groups["Name_columns"].append(col)
            
            # Определение столбцов с датами
            elif df[col].dtype == 'datetime64[ns]' or "date" in col.lower() or "дата" in col.lower():
                groups["Date_columns"].append(col)
            
            # Определение числовых столбцов
            elif pd.api.types.is_numeric_dtype(df[col]):
                groups["Numeric_columns"].append(col)
            
            # Определение категориальных столбцов (немного уникальных значений)
            elif df[col].dtype == 'object' and df[col].nunique() < 10:
                groups["Category_columns"].append(col)
            
            # Остальные текстовые столбцы
            elif df[col].dtype == 'object':
                groups["Text_columns"].append(col)
        
        # Удаляем пустые группы
        return {k: v for k, v in groups.items() if v}
    
    @staticmethod
    def process_text_file(file, encoding: str = 'utf-8', max_length: int = 10000) -> str:
        """
        Обрабатывает текстовый файл для использования в качестве контекста.
        
        Args:
            file: Текстовый файл (BytesIO или путь)
            encoding (str): Кодировка файла
            max_length (int): Максимальная длина текста
            
        Returns:
            str: Обработанный текст
        """
        try:
            if hasattr(file, 'read'):
                content = file.read().decode(encoding)
            else:
                with open(file, 'r', encoding=encoding) as f:
                    content = f.read()
            
            # Ограничиваем размер
            if len(content) > max_length:
                content = content[:max_length] + "... [содержимое сокращено]"
            
            return content
        except UnicodeDecodeError:
            # Пробуем другую кодировку, если utf-8 не сработала
            try:
                if hasattr(file, 'read'):
                    file.seek(0)  # Перемещаем указатель в начало
                    content = file.read().decode('cp1251')  # Пробуем кодировку Windows
                else:
                    with open(file, 'r', encoding='cp1251') as f:
                        content = f.read()
                
                if len(content) > max_length:
                    content = content[:max_length] + "... [содержимое сокращено]"
                
                return content
            except Exception as e:
                return f"[Ошибка чтения файла: {e}]"
        except Exception as e:
            return f"[Ошибка обработки файла: {e}]"
    
    @staticmethod
    def prepare_df_for_llm(df: pd.DataFrame, max_rows: int = 100, max_text_length: int = 200) -> str:
        """
        Подготавливает представление DataFrame для отправки в LLM.
        
        Args:
            df (pd.DataFrame): DataFrame для подготовки
            max_rows (int): Максимальное количество строк
            max_text_length (int): Максимальная длина текстовых значений
            
        Returns:
            str: Текстовое представление DataFrame
        """
        # Ограничиваем количество строк
        if len(df) > max_rows:
            preview_df = df.head(max_rows)
            summary = f"Показано {max_rows} из {len(df)} строк.\n\n"
        else:
            preview_df = df
            summary = ""
        
        # Ограничиваем длину текстовых значений
        for col in preview_df.select_dtypes(include=['object']).columns:
            preview_df[col] = preview_df[col].astype(str).apply(
                lambda x: x[:max_text_length] + "..." if len(x) > max_text_length else x
            )
        
        # Создаем StringIO для записи форматированного вывода
        output = io.StringIO()
        
        # Записываем базовую информацию
        output.write(f"DataFrame: {len(df)} строк, {len(df.columns)} столбцов\n")
        output.write(f"Столбцы: {', '.join(df.columns)}\n\n")
        output.write(summary)
        
        # Записываем данные в строковом формате
        output.write(preview_df.to_string())
        
        return output.getvalue()
    
    @staticmethod
    def auto_suggest_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Автоматически определяет подходящие типы анализа для DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame для анализа
            
        Returns:
            List[Dict[str, Any]]: Список рекомендуемых аналитических задач
        """
        suggestions = []
        
        # Базовая информация о размере данных
        row_count = len(df)
        col_count = len(df.columns)
        
        # Обнаружение числовых столбцов
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        # Обнаружение текстовых столбцов с длинным текстом
        text_cols = []
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].astype(str).str.len().mean() > 50:  # Средняя длина > 50 символов
                text_cols.append(col)
        
        # Обнаружение дат
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        
        # Предложения на основе обнаруженных данных
        
        # 1. Если есть числовые столбцы - статистический анализ
        if numeric_cols:
            suggestions.append({
                "type": "Статистический анализ",
                "description": "Базовая статистика, распределение и корреляции числовых данных",
                "columns": numeric_cols,
                "prompt_category": "Общая аналитика"
            })
        
        # 2. Если есть текстовые столбцы - анализ текста
        if text_cols:
            suggestions.append({
                "type": "Анализ текста",
                "description": "Извлечение ключевых моментов, саммаризация и категоризация текстовых данных",
                "columns": text_cols,
                "prompt_category": "Общая аналитика"
            })
            
            # Если похоже на отзывы/комментарии клиентов
            customer_keywords = ["отзыв", "комментарий", "обращение", "клиент", "пользователь", "отношение"]
            if any(any(keyword in col.lower() for keyword in customer_keywords) for col in text_cols):
                suggestions.append({
                    "type": "Анализ отзывов клиентов",
                    "description": "Анализ тональности, выявление проблем и предложений в отзывах",
                    "columns": text_cols,
                    "prompt_category": "Работа с клиентами"
                })
        
        # 3. Если есть даты - временной анализ
        if date_cols and numeric_cols:
            suggestions.append({
                "type": "Временной анализ",
                "description": "Анализ трендов и сезонности в данных, привязанных к датам",
                "columns": date_cols + numeric_cols,
                "prompt_category": "Финансы и отчетность"
            })
        
        # 4. Если много строк - поиск аномалий
        if row_count > 100 and numeric_cols:
            suggestions.append({
                "type": "Поиск аномалий",
                "description": "Выявление выбросов и нетипичных паттернов в данных",
                "columns": numeric_cols,
                "prompt_category": "Операционная деятельность"
            })
        
        # 5. Общий анализ таблицы
        suggestions.append({
            "type": "Общий анализ таблицы",
            "description": "Комплексный анализ всей таблицы с выявлением основных закономерностей",
            "columns": list(df.columns),
            "prompt_category": "Текстовая аналитика по всей таблице"
        })
        
        return suggestions

# Пример использования
if __name__ == "__main__":
    # Создаем тестовый DataFrame
    df = pd.DataFrame({
        'ID': range(1, 101),
        'Name': ['User ' + str(i) for i in range(1, 101)],
        'Date': pd.date_range(start='2023-01-01', periods=100),
        'Value': np.random.randint(1, 1000, 100),
        'Category': np.random.choice(['A', 'B', 'C'], 100),
        'Comment': ['This is a comment ' + str(i) for i in range(1, 101)]
    })
    
    # Используем класс DataProcessor
    processor = DataProcessor()
    
    # Анализируем DataFrame
    stats = processor.analyze_dataframe(df)
    print("Статистика DataFrame:")
    print(f"Форма: {stats['shape']}")
    print(f"Столбцы: {stats['columns']}")
    
    # Очищаем DataFrame
    cleaned_df = processor.clean_dataframe(df)
    
    # Предлагаем группировку столбцов
    groups = processor.suggest_column_groups(df)
    print("\nПредлагаемые группы столбцов:")
    for group, columns in groups.items():
        print(f"{group}: {columns}")
    
    # Автоматически предлагаем типы анализа
    suggestions = processor.auto_suggest_analysis(df)
    print("\nРекомендуемые типы анализа:")
    for suggestion in suggestions:
        print(f"{suggestion['type']}: {suggestion['description']}")
        print(f"  Столбцы: {suggestion['columns']}")