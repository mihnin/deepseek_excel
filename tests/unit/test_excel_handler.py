# tests/unit/test_excel_handler.py

import unittest
import pandas as pd
import io
import sys
import os

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.excel_handler import ExcelHandler

class TestExcelHandler(unittest.TestCase):
    def setUp(self):
        # Создаем тестовый DataFrame
        self.test_data = {
            'id': [1, 2, 3, 4, 5],
            'name': ['Иван', 'Мария', 'Петр', 'Анна', 'Сергей'],
            'age': [25, 32, 45, 18, None],
            'comment': [
                'Это хороший продукт',
                'Не соответствует ожиданиям',
                'Отличное качество, рекомендую',
                None,
                'Средний продукт по завышенной цене'
            ]
        }
        self.df = pd.DataFrame(self.test_data)
        
        # Создаем Excel-файл в памяти для тестов
        self.excel_data = io.BytesIO()
        self.df.to_excel(self.excel_data, index=False)
        self.excel_data.seek(0)
        
        # Инициализируем ExcelHandler
        self.handler = ExcelHandler()
    
    def test_load_excel(self):
        """Проверяет корректную загрузку Excel-файла"""
        loaded_df = self.handler.load_excel(self.excel_data)
        
        # Проверка размерности
        self.assertEqual(loaded_df.shape, self.df.shape)
        
        # Проверка наличия всех столбцов
        for col in self.df.columns:
            self.assertIn(col, loaded_df.columns)
        
        # Проверка содержимого
        pd.testing.assert_frame_equal(loaded_df, self.df, check_dtype=False)
    
    def test_analyze_dataframe(self):
        """Проверяет анализ DataFrame"""
        stats = self.handler.analyze_dataframe(self.df)
        
        # Проверка основных ключей в результате
        self.assertIn('shape', stats)
        self.assertIn('rows', stats)
        self.assertIn('columns', stats)
        self.assertIn('column_names', stats)
        self.assertIn('dtypes', stats)
        self.assertIn('missing_values', stats)
        self.assertIn('missing_percentage', stats)
        self.assertIn('has_issues', stats)
        
        # Проверка правильности значений
        self.assertEqual(stats['rows'], 5)
        self.assertEqual(stats['columns'], 4)
        self.assertEqual(set(stats['column_names']), set(['id', 'name', 'age', 'comment']))
        self.assertEqual(stats['missing_values']['age'], 1)
        self.assertEqual(stats['missing_values']['comment'], 1)
    
    def test_clean_dataframe(self):
        """Проверяет очистку DataFrame"""
        cleaned_df = self.handler.clean_dataframe(self.df)
        
        # Проверка, что все NaN значения заполнены
        self.assertEqual(cleaned_df['age'].isna().sum(), 0)
        self.assertEqual(cleaned_df['comment'].isna().sum(), 0)
        
        # Проверка, что число строк не изменилось (если не было дубликатов)
        self.assertEqual(len(cleaned_df), len(self.df))
    
    def test_suggest_target_columns(self):
        """Проверяет рекомендации целевых столбцов"""
        suggestions = self.handler.suggest_target_columns(self.df)
        
        # В нашем примере 'comment' должен быть предложен как целевой столбец для анализа
        self.assertIn('comment', suggestions)
        
        # 'id' и 'age' не должны предлагаться как целевые столбцы
        self.assertNotIn('id', suggestions)
        self.assertNotIn('age', suggestions)
    
    def test_suggest_additional_columns(self):
        """Проверяет рекомендации дополнительных столбцов"""
        suggestions = self.handler.suggest_additional_columns(self.df, 'comment')
        
        # 'name' и 'age' должны быть предложены как дополнительные столбцы
        self.assertIn('name', suggestions)
        self.assertIn('age', suggestions)
        
        # 'comment' не должен быть в списке, так как это целевой столбец
        self.assertNotIn('comment', suggestions)
    
    def test_save_to_excel(self):
        """Проверяет сохранение DataFrame в Excel"""
        output = self.handler.save_to_excel(self.df)
        
        # Проверяем, что вывод не пустой
        self.assertIsNotNone(output)
        self.assertGreater(len(output), 0)
        
        # Проверяем, что можем загрузить сохраненный Excel
        output_stream = io.BytesIO(output)
        loaded_df = pd.read_excel(output_stream)
        
        # Проверка размерности
        self.assertEqual(loaded_df.shape, self.df.shape)
        
        # Проверка наличия всех столбцов
        for col in self.df.columns:
            self.assertIn(col, loaded_df.columns)

if __name__ == '__main__':
    unittest.main()