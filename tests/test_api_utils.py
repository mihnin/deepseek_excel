# tests/test_api_utils.py
import unittest
from unittest.mock import MagicMock
import time
from modules.api_utils import APIUtils

class TestAPIUtils(unittest.TestCase):
    def test_retry_with_backoff_success_first_try(self):
        """Тест успешного выполнения с первой попытки"""
        mock_func = MagicMock(return_value=("success", None))
        
        result, error = APIUtils.retry_with_backoff(
            mock_func,
            max_retries=3,
            initial_delay=0.1
        )
        
        self.assertEqual(result, "success")
        self.assertIsNone(error)
        mock_func.assert_called_once()
    
    def test_retry_with_backoff_success_after_failures(self):
        """Тест успешного выполнения после нескольких неудачных попыток"""
        side_effects = [
            (None, "Error 1"),
            (None, "Error 2"),
            ("success", None)
        ]
        mock_func = MagicMock(side_effect=side_effects)
        
        result, error = APIUtils.retry_with_backoff(
            mock_func,
            max_retries=3,
            initial_delay=0.1
        )
        
        self.assertEqual(result, "success")
        self.assertIsNone(error)
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_with_backoff_all_failures(self):
        """Тест с неудачным результатом после всех попыток"""
        mock_func = MagicMock(return_value=(None, "Persistent error"))
        
        result, error = APIUtils.retry_with_backoff(
            mock_func,
            max_retries=3,
            initial_delay=0.1
        )
        
        self.assertIsNone(result)
        self.assertIn("Не удалось выполнить после 3 попыток", error)
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_with_backoff_exceptions(self):
        """Тест с исключениями вместо возвращения ошибок"""
        mock_func = MagicMock(side_effect=ValueError("Test exception"))
        
        result, error = APIUtils.retry_with_backoff(
            mock_func,
            max_retries=2,
            initial_delay=0.1
        )
        
        self.assertIsNone(result)
        self.assertIn("Test exception", error)
        self.assertEqual(mock_func.call_count, 2)
    
    def test_backoff_timing(self):
        """Тест корректности временных задержек"""
        mock_func = MagicMock(return_value=(None, "Error"))
        start_time = time.time()
        
        result, error = APIUtils.retry_with_backoff(
            mock_func,
            max_retries=3,
            initial_delay=0.1,
            backoff_factor=2.0
        )
        
        elapsed_time = time.time() - start_time
        # Ожидаемая задержка: 0.1 + 0.2 = 0.3 секунды плюс время выполнения
        self.assertGreaterEqual(elapsed_time, 0.3)
        self.assertEqual(mock_func.call_count, 3)

if __name__ == '__main__':
    unittest.main()