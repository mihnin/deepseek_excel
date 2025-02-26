# modules/file_utils.py
from io import BytesIO
from typing import List, Dict, Any, Optional, Union
import logging

class FileProcessor:
    """
    Класс для обработки различных типов файлов, используемых как дополнительный контекст.
    """
    
    def __init__(self):
        """Инициализация процессора файлов."""
        self.logger = logging.getLogger("FileProcessor")
    
    def process_context_files(self, files: List) -> List[BytesIO]:
        """
        Обрабатывает дополнительные файлы для контекста, подготавливая их для чтения.
        
        Args:
            files (List): Список загруженных файлов
            
        Returns:
            List[BytesIO]: Список обработанных файлов в памяти
        """
        if not files:
            return []
        
        processed_files = []
        
        for file in files:
            try:
                # Читаем содержимое файла в память
                file_bytes = BytesIO(file.read())
                file_bytes.name = file.name
                processed_files.append(file_bytes)
                
                # Возвращаем указатель в начало для последующего чтения
                file.seek(0)
                
            except Exception as e:
                self.logger.error(f"Ошибка при обработке файла {file.name}: {str(e)}")
        
        return processed_files
    
    def extract_text_from_file(self, file, max_length: int = 10000, encoding: str = 'utf-8') -> str:
        """
        Извлекает текст из файла с обработкой различных кодировок.
        
        Args:
            file: Файл для чтения (BytesIO или путь)
            max_length (int): Максимальная длина извлекаемого текста
            encoding (str): Кодировка для чтения файла
            
        Returns:
            str: Извлеченный текст или сообщение об ошибке
        """
        if not file:
            return ""
            
        try:
            # Если файл - объект BytesIO или аналогичный
            if hasattr(file, 'read'):
                # Сохраняем текущую позицию, чтобы можно было вернуться
                original_position = file.tell()
                content = file.read().decode(encoding)
                file.seek(original_position)  # Возвращаем позицию
            else:
                # Файл - путь к файлу
                with open(file, 'r', encoding=encoding) as f:
                    content = f.read()
            
            # Ограничиваем длину текста
            if len(content) > max_length:
                content = content[:max_length] + "... [содержимое сокращено]"
            
            return content
            
        except UnicodeDecodeError:
            # Если не удалось декодировать с указанной кодировкой, пробуем другие
            try:
                if hasattr(file, 'read'):
                    file.seek(original_position)
                    content = file.read().decode('cp1251')  # Пробуем Windows-1251
                    file.seek(original_position)
                else:
                    with open(file, 'r', encoding='cp1251') as f:
                        content = f.read()
                
                if len(content) > max_length:
                    content = content[:max_length] + "... [содержимое сокращено]"
                
                return content
            except Exception as e:
                return f"[Ошибка чтения файла: не удалось определить кодировку]"
        except Exception as e:
            return f"[Ошибка обработки файла: {str(e)}]"
    
    def prepare_context_for_analysis(self, files: List, include_file_names: bool = True) -> str:
        """
        Подготавливает дополнительные файлы как контекст для анализа.
        
        Args:
            files (List): Список файлов для обработки
            include_file_names (bool): Включать имена файлов в контекст
            
        Returns:
            str: Подготовленный контекст для передачи в LLM
        """
        if not files:
            return ""
        
        context_text = "Дополнительные контекстные файлы:\n\n"
        
        for file in files:
            try:
                file_name = getattr(file, 'name', 'Неизвестный файл')
                
                # Извлекаем текст из файла
                content = self.extract_text_from_file(file)
                
                # Добавляем информацию о файле и его содержимое в контекст
                if include_file_names:
                    context_text += f"--- Файл: {file_name} ---\n"
                
                context_text += f"{content}\n\n"
                
            except Exception as e:
                self.logger.error(f"Ошибка при подготовке контекста из файла: {str(e)}")
                if include_file_names:
                    context_text += f"--- Файл: {getattr(file, 'name', 'Неизвестный файл')} --- [Не удалось прочитать содержимое]\n\n"
        
        return context_text
    
    def detect_file_type(self, file_name: str) -> str:
        """
        Определяет тип файла по его расширению.
        
        Args:
            file_name (str): Имя файла
            
        Returns:
            str: Тип файла ('text', 'csv', 'json', 'markdown', 'unknown')
        """
        extension = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        if extension in ['txt', 'log']:
            return 'text'
        elif extension == 'csv':
            return 'csv'
        elif extension == 'json':
            return 'json'
        elif extension in ['md', 'markdown']:
            return 'markdown'
        else:
            return 'unknown'
    
    def summarize_files(self, files: List) -> Dict[str, Any]:
        """
        Создает сводку о загруженных файлах.
        
        Args:
            files (List): Список файлов
            
        Returns:
            Dict[str, Any]: Сводная информация о файлах
        """
        if not files:
            return {"count": 0, "files": []}
        
        summary = {
            "count": len(files),
            "files": []
        }
        
        for file in files:
            file_name = getattr(file, 'name', 'Неизвестный файл')
            file_size = getattr(file, 'size', 0)
            file_type = self.detect_file_type(file_name)
            
            summary["files"].append({
                "name": file_name,
                "size": file_size,
                "type": file_type
            })
        
        return summary