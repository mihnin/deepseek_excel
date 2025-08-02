# tests/unit/test_api_utils.py

import unittest
from unittest.mock import MagicMock
import time
import sys
import os

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.services.api_utils import APIUtils

class TestAPIUtils(unittest.TestCase):
    def setUp(self):
        self.api_utils = APIUtils()
    
    def test_retry_on_failure(self):
        """Проверяет механизм повторных попыток при ошибках"""
        # Создаем функцию, которая падает первые 2 раза
        mock_func = MagicMock(side_effect=[
            Exception("Первая ошибка"),
            Exception("Вторая ошибка"),
            "Успешный результат"
        ])
        
        # Вызываем через retry_on_failure
        result = self.api_utils.retry_on_failure(mock_func, max_retries=3)
        
        # Проверяем результат
        self.assertEqual(result, "Успешный результат")
        
        # Проверяем, что функция была вызвана 3 раза
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_on_failure_max_retries(self):
        """Проверяет поведение при превышении максимального числа попыток"""
        # Функция, которая всегда падает
        mock_func = MagicMock(side_effect=Exception("Постоянная ошибка"))
        
        # Вызываем через retry_on_failure
        with self.assertRaises(Exception) as context:
            self.api_utils.retry_on_failure(mock_func, max_retries=2)
        
        # Проверяем, что была выброшена правильная ошибка
        self.assertIn("Постоянная ошибка", str(context.exception))
        
        # Проверяем, что функция была вызвана правильное количество раз
        self.assertEqual(mock_func.call_count, 2)
    
    def test_rate_limiter(self):
        """Проверяет работу ограничителя скорости"""
        # Начальное время
        start_time = time.time()
        
        # Выполняем несколько вызовов
        for _ in range(3):
            self.api_utils.rate_limiter(calls_per_second=10)
        
        # Проверяем, что прошло минимальное время
        elapsed = time.time() - start_time
        
        # С учетом 10 вызовов в секунду, 3 вызова должны занять минимум 0.2 секунды
        # (между вызовами должна быть задержка 0.1 секунды)
        self.assertGreaterEqual(elapsed, 0.2)
    
    def test_batch_processor(self):
        """Проверяет пакетную обработку данных"""
        # Тестовые данные
        items = list(range(10))
        
        # Функция обработки
        def process_func(batch):
            return [x * 2 for x in batch]
        
        # Обрабатываем пакетами
        results = self.api_utils.batch_processor(items, process_func, batch_size=3)
        
        # Проверяем результаты
        expected = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
        self.assertEqual(results, expected)
    
    def test_batch_processor_with_error(self):
        """Проверяет обработку ошибок в пакетной обработке"""
        items = list(range(5))
        
        # Функция, которая падает на определенном значении
        def process_func(batch):
            if 3 in batch:
                raise ValueError("Ошибка на значении 3")
            return [x * 2 for x in batch]
        
        # Проверяем, что исключение пробрасывается
        with self.assertRaises(ValueError) as context:
            self.api_utils.batch_processor(items, process_func, batch_size=2)
        
        self.assertIn("Ошибка на значении 3", str(context.exception))
    
    def test_validate_api_response(self):
        """Проверяет валидацию API ответов"""
        # Валидный ответ
        valid_response = {
            "status": "success",
            "data": {"result": "test"}
        }
        
        result = self.api_utils.validate_api_response(valid_response)
        self.assertTrue(result)
        
        # Невалидный ответ (пустой)
        invalid_response = {}
        result = self.api_utils.validate_api_response(invalid_response)
        self.assertFalse(result)
        
        # Невалидный ответ (None)
        result = self.api_utils.validate_api_response(None)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()