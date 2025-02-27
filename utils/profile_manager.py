# utils/profile_manager.py
import streamlit as st
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

class ProfileManager:
    """
    Класс для управления сохранением и загрузкой профилей настроек.
    """
    
    def __init__(self, profiles_dir: str = "profiles"):
        """
        Инициализирует менеджер профилей.
        
        Args:
            profiles_dir (str): Директория для хранения профилей
        """
        self.profiles_dir = profiles_dir
        
        # Создаем директорию, если её нет
        os.makedirs(profiles_dir, exist_ok=True)
        
        # Инициализируем session_state для профилей, если его нет
        if "saved_profiles" not in st.session_state:
            st.session_state["saved_profiles"] = {}
            
            # Загружаем профили из файлов при первом запуске
            self.load_profiles_from_disk()
    
    def save_profile(self, profile_name: str, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет профиль настроек.
        
        Args:
            profile_name (str): Название профиля
            settings (Dict[str, Any]): Настройки для сохранения
            
        Returns:
            bool: True если профиль успешно сохранен, иначе False
        """
        if not profile_name:
            return False
        
        try:
            # Добавляем дату сохранения
            settings["_saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Сохраняем в session_state
            st.session_state["saved_profiles"][profile_name] = settings
            
            # Сохраняем на диск
            profile_path = os.path.join(self.profiles_dir, f"{profile_name.replace(' ', '_')}.json")
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении профиля: {e}")
            return False
    
    def load_profile(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """
        Загружает профиль настроек.
        
        Args:
            profile_name (str): Название профиля
            
        Returns:
            Optional[Dict[str, Any]]: Настройки профиля или None, если профиль не найден
        """
        if not profile_name or profile_name not in st.session_state["saved_profiles"]:
            return None
        
        try:
            return st.session_state["saved_profiles"][profile_name]
        except Exception as e:
            print(f"Ошибка при загрузке профиля: {e}")
            return None
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Удаляет профиль настроек.
        
        Args:
            profile_name (str): Название профиля
            
        Returns:
            bool: True если профиль успешно удален, иначе False
        """
        if not profile_name or profile_name not in st.session_state["saved_profiles"]:
            return False
        
        try:
            # Удаляем из session_state
            del st.session_state["saved_profiles"][profile_name]
            
            # Удаляем файл, если он существует
            profile_path = os.path.join(self.profiles_dir, f"{profile_name.replace(' ', '_')}.json")
            if os.path.exists(profile_path):
                os.remove(profile_path)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при удалении профиля: {e}")
            return False
    
    def get_profile_list(self) -> List[str]:
        """
        Возвращает список доступных профилей.
        
        Returns:
            List[str]: Список названий профилей
        """
        return list(st.session_state["saved_profiles"].keys())
    
    def load_profiles_from_disk(self) -> None:
        """
        Загружает все профили из директории с профилями.
        """
        try:
            if os.path.exists(self.profiles_dir):
                for filename in os.listdir(self.profiles_dir):
                    if filename.endswith(".json"):
                        profile_path = os.path.join(self.profiles_dir, filename)
                        profile_name = filename[:-5].replace("_", " ")  # Убираем .json и восстанавливаем пробелы
                        
                        try:
                            with open(profile_path, "r", encoding="utf-8") as f:
                                profile_data = json.load(f)
                                st.session_state["saved_profiles"][profile_name] = profile_data
                        except Exception as e:
                            print(f"Ошибка при загрузке профиля {profile_name}: {e}")
        except Exception as e:
            print(f"Ошибка при загрузке профилей с диска: {e}")
    
    def render_ui(self) -> None:
        """
        Отображает UI для управления профилями.
        """
        with st.expander("Управление профилями"):
            # Секция сохранения профиля
            st.subheader("Сохранить текущие настройки")
            profile_name = st.text_input("Название профиля", key="new_profile_name")
            
            save_clicked = st.button("Сохранить профиль")
            if save_clicked:
                if profile_name:
                    # Собираем текущие настройки
                    current_settings = {
                        "provider_type": st.session_state.get("provider_type", "cloud"),
                        "model": st.session_state.get("model", "deepseek-chat"),
                        "local_model": st.session_state.get("local_model", "llama2"),
                        "temperature": st.session_state.get("temperature", 0.7),
                        "max_tokens": st.session_state.get("max_tokens", 300),
                        "top_p": st.session_state.get("top_p", 1.0),
                        "frequency_penalty": st.session_state.get("frequency_penalty", 0.0),
                        "presence_penalty": st.session_state.get("presence_penalty", 0.0),
                        "mode": st.session_state.get("mode", "Построчный анализ"),
                        "custom_prompt": st.session_state.get("custom_prompt", ""),
                        "cloud_base_url": st.session_state.get("cloud_base_url", "https://api.deepseek.com"),
                        "local_provider": st.session_state.get("local_provider", "ollama"),
                        "local_base_url": st.session_state.get("local_base_url", "http://localhost:11434")
                    }
                    
                    if self.save_profile(profile_name, current_settings):
                        st.success(f"Профиль '{profile_name}' успешно сохранен!")
                    else:
                        st.error("Не удалось сохранить профиль")
                else:
                    st.warning("Введите название профиля")
            
            # Секция загрузки профиля
            st.subheader("Загрузить сохраненный профиль")
            profile_options = self.get_profile_list()
            
            if profile_options:
                selected_profile = st.selectbox(
                    "Выберите профиль", 
                    profile_options, 
                    key="load_profile_select"
                )
                
                # Кнопки загрузки и удаления без колонок
                if st.button("Загрузить профиль"):
                    settings = self.load_profile(selected_profile)
                    if settings:
                        # Загрузка настроек в session_state
                        for key, value in settings.items():
                            if not key.startswith("_"):  # Пропускаем служебные поля
                                st.session_state[key] = value
                        st.success(f"Профиль '{selected_profile}' загружен!")
                    else:
                        st.error("Не удалось загрузить профиль")
                
                if st.button("Удалить профиль", type="secondary"):
                    if self.delete_profile(selected_profile):
                        st.success(f"Профиль '{selected_profile}' удален!")
                    else:
                        st.error("Не удалось удалить профиль")
            else:
                st.info("Нет сохраненных профилей")