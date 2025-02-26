# ui/export_view.py
import streamlit as st
from modules.export_utils import ExportManager
from datetime import datetime

def render_export_ui(df, table_analysis=None):
    """Отображает UI для экспорта результатов"""
    st.subheader("Экспорт результатов")
    
    # Создаем уникальное имя файла с текущей датой/временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"results_{timestamp}"
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel
        excel_data = ExportManager.to_excel(df)
        ExportManager.create_download_button(
            excel_data, 
            f"{base_filename}.xlsx", 
            "📥 Скачать как Excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # JSON
        json_data = ExportManager.to_json(df)
        ExportManager.create_download_button(
            json_data, 
            f"{base_filename}.json", 
            "📥 Скачать как JSON",
            "application/json"
        )
    
    with col2:
        # CSV
        csv_data = ExportManager.to_csv(df)
        ExportManager.create_download_button(
            csv_data, 
            f"{base_filename}.csv", 
            "📥 Скачать как CSV",
            "text/csv"
        )
        
        # Word (если есть анализ всей таблицы)
        if table_analysis:
            word_data = ExportManager.to_word(df, table_analysis)
            ExportManager.create_download_button(
                word_data, 
                f"{base_filename}.docx", 
                "📥 Скачать отчет Word",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )