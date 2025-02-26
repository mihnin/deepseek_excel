# run_tests.py
import unittest
import sys
import os

def run_tests():
    """Запускает все тесты в директории tests/"""
    # Добавляем текущую директорию в путь для импортов
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Находим и запускаем все тесты
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    
    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Возвращаем код статуса (0 - успех, 1 - неудача)
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())