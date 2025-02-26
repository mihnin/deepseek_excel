# tests/test_excel_handler.py

import unittest
import pandas as pd
import io
from modules.excel_handler import ExcelHandler

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

# tests/test_prompt_library.py

import unittest
from modules.prompt_library import get_business_prompts, customize_prompt

class TestPromptLibrary(unittest.TestCase):
    def test_get_business_prompts(self):
        """Проверяет получение библиотеки промптов"""
        structured_prompts, flat_prompts = get_business_prompts()
        
        # Проверка структуры
        self.assertIsInstance(structured_prompts, dict)
        self.assertIsInstance(flat_prompts, dict)
        
        # Проверка наличия основных категорий
        self.assertIn("Общая аналитика", structured_prompts)
        self.assertIn("Работа с клиентами", structured_prompts)
        self.assertIn("Маркетинг", structured_prompts)
        
        # Проверка, что в плоском словаре есть промпты из всех категорий
        for category, prompts in structured_prompts.items():
            for prompt_name, prompt_text in prompts.items():
                flat_key = f"{category}: {prompt_name}"
                self.assertIn(flat_key, flat_prompts)
                self.assertEqual(flat_prompts[flat_key], prompt_text)
    
    def test_customize_prompt(self):
        """Проверяет кастомизацию промпта с контекстом"""
        base_prompt = "Проанализируй текст и выдели ключевые моменты:"
        
        # Тест с целевым столбцом
        context1 = {
            "target_column": "комментарий"
        }
        result1 = customize_prompt(base_prompt, context1)
        self.assertIn("Проанализируй текст и выдели ключевые моменты:", result1)
        self.assertIn("Целевой столбец для анализа: комментарий", result1)
        
        # Тест с дополнительными столбцами
        context2 = {
            "target_column": "отзыв",
            "additional_columns": ["дата", "рейтинг"]
        }
        result2 = customize_prompt(base_prompt, context2)
        self.assertIn("Целевой столбец для анализа: отзыв", result2)
        self.assertIn("Дополнительный контекст из столбцов: дата, рейтинг", result2)
        
        # Тест с данными строки
        context3 = {
            "target_column": "текст",
            "row_data": {
                "текст": "Это пример текста для анализа",
                "категория": "Пример",
                "приоритет": "Высокий"
            }
        }
        result3 = customize_prompt(base_prompt, context3)
        self.assertIn("Данные для анализа:", result3)
        self.assertIn("текст: Это пример текста для анализа", result3)
        self.assertIn("категория: Пример", result3)
        self.assertIn("приоритет: Высокий", result3)

# tests/test_unified_llm.py

import unittest
from unittest.mock import MagicMock, patch
from modules.unified_llm import UnifiedLLMProvider

class TestUnifiedLLM(unittest.TestCase):
    @patch('modules.unified_llm.LocalLLMProvider')
    @patch('modules.llm_integration.LLMServiceProvider')
    def test_init_cloud_provider(self, mock_cloud_provider, mock_local_provider):
        """Проверяет инициализацию облачного провайдера"""
        config = {
            "provider_type": "cloud",
            "cloud_api_key": "test-api-key",
            "cloud_base_url": "https://test-api.com"
        }
        
        # Инициализация UnifiedLLMProvider с облачным конфигом
        provider = UnifiedLLMProvider(config)
        
        # Проверка, что был создан облачный провайдер с правильными параметрами
        mock_cloud_provider.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://test-api.com"
        )
        
        # Проверка, что локальный провайдер не был создан
        mock_local_provider.assert_not_called()
    
    @patch('modules.unified_llm.LocalLLMProvider')
    @patch('modules.llm_integration.LLMServiceProvider', side_effect=ImportError)
    def test_init_cloud_provider_error(self, mock_cloud_provider, mock_local_provider):
        """Проверяет обработку ошибки при инициализации облачного провайдера"""
        config = {
            "provider_type": "cloud",
            "cloud_api_key": "test-api-key"
        }
        
        # Инициализация UnifiedLLMProvider с облачным конфигом
        provider = UnifiedLLMProvider(config)
        
        # Проверка, что provider равен None при ошибке
        self.assertIsNone(provider.provider)
    
    @patch('modules.unified_llm.LocalLLMProvider')
    @patch('modules.llm_integration.LLMServiceProvider')
    def test_init_local_provider(self, mock_cloud_provider, mock_local_provider):
        """Проверяет инициализацию локального провайдера"""
        config = {
            "provider_type": "local",
            "local_provider": "ollama",
            "local_base_url": "http://localhost:11434"
        }
        
        # Инициализация UnifiedLLMProvider с локальным конфигом
        provider = UnifiedLLMProvider(config)
        
        # Проверка, что был создан локальный провайдер с правильными параметрами
        mock_local_provider.assert_called_once_with(
            provider="ollama",
            base_url="http://localhost:11434"
        )
        
        # Проверка, что облачный провайдер не был создан
        mock_cloud_provider.assert_not_called()
    
    @patch('modules.unified_llm.LocalLLMProvider')
    @patch('modules.llm_integration.LLMServiceProvider')
    def test_switch_provider(self, mock_cloud_provider, mock_local_provider):
        """Проверяет переключение между провайдерами"""
        provider = UnifiedLLMProvider({"provider_type": "cloud", "cloud_api_key": "test-key"})
        
        # Сбрасываем счетчики вызовов
        mock_cloud_provider.reset_mock()
        mock_local_provider.reset_mock()
        
        # Переключаемся на локальный провайдер
        provider.switch_provider("local", local_provider="ollama")
        
        # Проверка, что был создан локальный провайдер
        mock_local_provider.assert_called_once()
        self.assertEqual(provider.config["provider_type"], "local")
        self.assertEqual(provider.config["local_provider"], "ollama")
    
    @patch('modules.unified_llm.LocalLLMProvider')
    def test_get_available_models(self, mock_local_provider):
        """Проверяет получение списка доступных моделей"""
        # Настраиваем мок для возврата списка моделей
        mock_instance = mock_local_provider.return_value
        mock_instance.get_available_models.return_value = [
            {"id": "model1", "name": "Model 1"},
            {"id": "model2", "name": "Model 2"}
        ]
        
        provider = UnifiedLLMProvider({"provider_type": "local"})
        models = provider.get_available_models()
        
        # Проверка, что вызван правильный метод
        mock_instance.get_available_models.assert_called_once()
        
        # Проверка возвращаемого значения
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0]["id"], "model1")
        self.assertEqual(models[1]["name"], "Model 2")
    
    @patch('modules.unified_llm.LocalLLMProvider')
    def test_chat_completion(self, mock_local_provider):
        """Проверяет выполнение запроса к LLM"""
        # Настраиваем мок для возврата ответа
        mock_instance = mock_local_provider.return_value
        mock_instance.chat_completion.return_value = ("Test response", None)
        
        provider = UnifiedLLMProvider({"provider_type": "local"})
        messages = [{"role": "user", "content": "Test prompt"}]
        response, error = provider.chat_completion(messages=messages)
        
        # Проверка вызова метода
        mock_instance.chat_completion.assert_called_once_with(
            messages=messages,
            model="llama2",  # Значение по умолчанию для локального провайдера
            temperature=0.7,
            max_tokens=300,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            max_retries=3,
            retry_delay=2
        )
        
        # Проверка возвращаемого значения
        self.assertEqual(response, "Test response")
        self.assertIsNone(error)
    
    @patch('modules.unified_llm.LocalLLMProvider')
    def test_is_available(self, mock_local_provider):
        """Проверяет метод проверки доступности провайдера"""
        # Настраиваем мок
        mock_instance = mock_local_provider.return_value
        mock_instance.ping.return_value = True
        
        provider = UnifiedLLMProvider({"provider_type": "local"})
        available = provider.is_available()
        
        # Проверка вызова метода
        mock_instance.ping.assert_called_once()
        
        # Проверка возвращаемого значения
        self.assertTrue(available)

if __name__ == '__main__':
    unittest.main()