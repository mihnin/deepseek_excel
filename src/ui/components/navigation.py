import streamlit as st
from urllib.parse import urlencode

def navigate_to_tab(tab_name):
    """
    Переходит на указанную вкладку с обновлением URL параметров.
    
    Args:
        tab_name (str): Имя вкладки для перехода
    """
    # Сохраняем активную вкладку в session_state
    st.session_state.active_tab = tab_name
    
    # Обновляем URL параметры с использованием нового API
    st.query_params["tab"] = tab_name
    
    # Перезагрузка приложения для применения изменений
    st.experimental_rerun()

def get_active_tab_from_url():
    """
    Получает активную вкладку из URL параметров.
    
    Returns:
        str: Имя активной вкладки или None, если параметр не задан
    """
    # Используем новый синтаксис для получения параметров запроса
    tab_param = st.query_params.get("tab", None)
    return tab_param

def initialize_navigation():
    """
    Инициализирует механизм навигации, проверяя URL параметры
    и устанавливая соответствующую активную вкладку.
    """
    # Если активная вкладка ещё не установлена в session_state
    if "active_tab" not in st.session_state:
        # Проверяем URL параметры
        active_tab = get_active_tab_from_url()
        
        # Если параметр tab задан в URL, используем его
        if active_tab in ["tab1", "tab2", "tab3"]:
            st.session_state.active_tab = active_tab
        else:
            # По умолчанию первая вкладка
            st.session_state.active_tab = "tab1"
    else:
        # Синхронизируем URL с текущей активной вкладкой
        active_tab = st.session_state.active_tab
        curr_tab = get_active_tab_from_url()
        
        # Если активная вкладка отличается от URL, обновляем URL
        if curr_tab != active_tab:
            st.query_params["tab"] = active_tab
