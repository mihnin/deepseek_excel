#!/usr/bin/env python3
# scripts/run_tests.py

import unittest
import sys
import os

# Добавляем корневую директорию проекта в path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

def run_tests():
    """Запускает все тесты проекта"""
    # Создаем тестовый загрузчик
    loader = unittest.TestLoader()
    
    # Находим все тесты в директории tests/unit
    test_dir = os.path.join(project_root, 'tests', 'unit')
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Создаем runner с подробным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Запускаем тесты
    result = runner.run(suite)
    
    # Возвращаем 0 если все тесты прошли, иначе 1
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())