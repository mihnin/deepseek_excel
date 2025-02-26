# utils/config_manager.py
import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """
    Класс для управления конфигурацией приложения.
    Загружает настройки из файла по умолчанию и пользовательского файла.
    """
    
    def __init__(self, default_config_path: str = "config/default_config.json", 
                 user_config_path: Optional[str] = None):
        """
        Инициализирует менеджер конфигурации.
        
        Args:
            default_config_path (str): Путь к файлу конфигурации по умолчанию
            user_config_path (Optional[str]): Путь к пользовательскому файлу конфигурации
        """
        self.default_config_path = default_config_path
        self.user_config_path = user_config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Загружает и объединяет настройки из файлов конфигурации.
        
        Returns:
            Dict[str, Any]: Объединенная конфигурация
        """
        # Загрузка настроек по умолчанию
        try:
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                default_config = json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке конфигурации по умолчанию: {e}")
            default_config = {}
        
        # Загрузка пользовательских настроек
        user_config = {}
        if self.user_config_path and os.path.exists(self.user_config_path):
            try:
                with open(self.user_config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
            except Exception as e:
                print(f"Ошибка при загрузке пользовательской конфигурации: {e}")
        
        # Объединение конфигураций
        # Рекурсивно объединяем словари
        return self._merge_dicts(default_config, user_config)
    
    def _merge_dicts(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Рекурсивно объединяет два словаря.
        
        Args:
            dict1 (Dict[str, Any]): Первый словарь (базовый)
            dict2 (Dict[str, Any]): Второй словарь (приоритетный)
            
        Returns:
            Dict[str, Any]: Объединенный словарь
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Получает значение настройки по пути.
        
        Args:
            path (str): Путь к настройке в формате "section.subsection.key"
            default (Any): Значение по умолчанию, если настройка не найдена
            
        Returns:
            Any: Значение настройки или default, если не найдено
        """
        parts = path.split('.')
        current = self.config
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        
        return current
    
    def set(self, path: str, value: Any) -> None:
        """
        Устанавливает значение настройки по пути.
        
        Args:
            path (str): Путь к настройке в формате "section.subsection.key"
            value (Any): Новое значение
        """
        parts = path.split('.')
        current = self.config
        
        # Проходим до предпоследней части пути
        for i, part in enumerate(parts[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        # Устанавливаем значение последней части
        current[parts[-1]] = value
    
    def save_user_config(self, path: Optional[str] = None) -> bool:
        """
        Сохраняет пользовательскую конфигурацию в файл.
        
        Args:
            path (Optional[str]): Путь к файлу или None для использования self.user_config_path
            
        Returns:
            bool: True если успешно сохранено, иначе False
        """
        save_path = path or self.user_config_path
        
        if not save_path:
            return False
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении конфигурации: {e}")
            return False