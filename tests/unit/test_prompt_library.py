# tests/unit/test_prompt_library.py

import unittest
import sys
import os

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.services.prompt_library import get_business_prompts, customize_prompt

class TestPromptLibrary(unittest.TestCase):
    def test_get_business_prompts(self):
        """Проверяет получение библиотеки промптов"""
        structured_prompts, flat_prompts = get_business_prompts()
        
        # Проверка структуры
        self.assertIsInstance(structured_prompts, dict)
        self.assertIsInstance(flat_prompts, list)
        
        # Проверка наличия основных категорий
        expected_categories = ['Анализ данных', 'Обработка текста', 'Бизнес-аналитика', 'Отчетность']
        for category in expected_categories:
            self.assertIn(category, structured_prompts)
        
        # Проверка, что flat_prompts не пустой
        self.assertGreater(len(flat_prompts), 0)
        
        # Проверка структуры элементов flat_prompts
        for prompt in flat_prompts:
            self.assertIn('value', prompt)
            self.assertIn('label', prompt)
    
    def test_customize_prompt(self):
        """Проверяет кастомизацию промптов"""
        base_prompt = "Проанализируй данные в столбце {column}"
        column_name = "Продажи"
        
        result = customize_prompt(base_prompt, column_name)
        
        # Проверка замены плейсхолдера
        self.assertEqual(result, "Проанализируй данные в столбце Продажи")
        
        # Тест с множественными плейсхолдерами
        base_prompt = "Сравни {column} и {column}"
        result = customize_prompt(base_prompt, column_name)
        self.assertEqual(result, "Сравни Продажи и Продажи")
        
        # Тест без плейсхолдеров
        base_prompt = "Простой промпт без замен"
        result = customize_prompt(base_prompt, column_name)
        self.assertEqual(result, "Простой промпт без замен")
    
    def test_prompt_structure_integrity(self):
        """Проверяет целостность структуры промптов"""
        structured_prompts, flat_prompts = get_business_prompts()
        
        # Подсчитываем общее количество промптов в structured
        total_structured = 0
        for category, prompts in structured_prompts.items():
            self.assertIsInstance(prompts, list)
            total_structured += len(prompts)
            
            # Проверка структуры каждого промпта
            for prompt in prompts:
                self.assertIsInstance(prompt, dict)
                self.assertIn('name', prompt)
                self.assertIn('prompt', prompt)
        
        # Проверка, что flat_prompts содержит все промпты
        self.assertEqual(len(flat_prompts), total_structured)

if __name__ == '__main__':
    unittest.main()