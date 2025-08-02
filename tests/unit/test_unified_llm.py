# tests/unit/test_unified_llm.py

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.llm.unified_provider import UnifiedLLM as UnifiedLLMProvider

class TestUnifiedLLM(unittest.TestCase):
    @patch('src.llm.unified_provider.LocalLLMProvider')
    def test_init_local_provider(self, mock_local_provider):
        """Проверяет инициализацию локального провайдера"""
        config = {
            "provider_type": "local",
            "local_provider": "ollama",
            "local_base_url": "http://localhost:11434"
        }
        
        provider = UnifiedLLMProvider(config)
        
        # Проверка, что локальный провайдер был создан
        mock_local_provider.assert_called_once()
        self.assertEqual(provider.config["provider_type"], "local")
    
    @patch('src.llm.unified_provider.LocalLLMProvider')
    def test_chat_completion_local(self, mock_local_provider):
        """Проверяет вызов chat_completion для локального провайдера"""
        # Настройка мока
        mock_instance = MagicMock()
        mock_instance.chat_completion.return_value = ("Ответ от модели", {"usage": "test"})
        mock_local_provider.return_value = mock_instance
        
        config = {
            "provider_type": "local",
            "local_provider": "ollama"
        }
        
        provider = UnifiedLLMProvider(config)
        result = provider.chat_completion("Тестовый запрос", model="llama2")
        
        # Проверка вызова
        mock_instance.chat_completion.assert_called_once_with("Тестовый запрос", model="llama2")
        self.assertEqual(result, ("Ответ от модели", {"usage": "test"}))
    
    @patch('src.llm.unified_provider.LocalLLMProvider')
    def test_analyze_rows_batch(self, mock_local_provider):
        """Проверяет пакетную обработку строк"""
        # Настройка мока
        mock_instance = MagicMock()
        mock_instance.chat_completion.return_value = ("Анализ строки", {"usage": "test"})
        mock_local_provider.return_value = mock_instance
        
        config = {
            "provider_type": "local",
            "local_provider": "ollama"
        }
        
        provider = UnifiedLLMProvider(config)
        
        rows = [
            {"id": 1, "text": "Первая строка"},
            {"id": 2, "text": "Вторая строка"}
        ]
        
        results = provider.analyze_rows_batch(rows, "Проанализируй: {row}")
        
        # Проверка количества результатов
        self.assertEqual(len(results), 2)
        
        # Проверка структуры результатов
        for result in results:
            self.assertIn('row_data', result)
            self.assertIn('analysis', result)
            self.assertIn('usage', result)
    
    @patch('src.llm.unified_provider.LocalLLMProvider')
    def test_analyze_full_table(self, mock_local_provider):
        """Проверяет анализ полной таблицы"""
        # Настройка мока
        mock_instance = MagicMock()
        mock_instance.chat_completion.return_value = ("Анализ таблицы", {"tokens": 100})
        mock_local_provider.return_value = mock_instance
        
        config = {
            "provider_type": "local",
            "local_provider": "ollama"
        }
        
        provider = UnifiedLLMProvider(config)
        
        table_data = "col1,col2\nval1,val2\nval3,val4"
        result = provider.analyze_full_table(table_data, "Проанализируй таблицу")
        
        # Проверка вызова
        mock_instance.chat_completion.assert_called_once()
        
        # Проверка результата
        self.assertEqual(result[0], "Анализ таблицы")
        self.assertEqual(result[1], {"tokens": 100})
    
    @patch('src.llm.unified_provider.LocalLLMProvider')
    def test_switch_provider(self, mock_local_provider):
        """Проверяет переключение между провайдерами"""
        config = {
            "provider_type": "local",
            "local_provider": "ollama"
        }
        
        provider = UnifiedLLMProvider(config)
        
        # Изначально локальный
        self.assertEqual(provider.config["provider_type"], "local")
        
        # Переключаем на облачный
        new_config = {
            "provider_type": "cloud",
            "cloud_api_key": "test_key"
        }
        
        provider.switch_provider(new_config)
        self.assertEqual(provider.config["provider_type"], "cloud")
    
    @patch('src.llm.unified_provider.LocalLLMProvider')
    def test_error_handling(self, mock_local_provider):
        """Проверяет обработку ошибок"""
        # Настройка мока для генерации ошибки
        mock_instance = MagicMock()
        mock_instance.chat_completion.side_effect = Exception("Тестовая ошибка")
        mock_local_provider.return_value = mock_instance
        
        config = {
            "provider_type": "local",
            "local_provider": "ollama"
        }
        
        provider = UnifiedLLMProvider(config)
        
        # Проверка, что исключение обрабатывается корректно
        with self.assertRaises(Exception) as context:
            provider.chat_completion("Тестовый запрос")
        
        self.assertIn("Тестовая ошибка", str(context.exception))

if __name__ == '__main__':
    unittest.main()