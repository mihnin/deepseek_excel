# ui/visualization_view.py

import streamlit as st
from src.services.visualization import DataVisualizer

def display_visualizations(df, result_column):
    """Отображает визуализации для результатов анализа"""
    st.subheader("Визуализация результатов")
    
    # Проверяем, есть ли в результатах анализа извлеченная тональность
    if 'тональность' in df.columns or 'sentiment' in df.columns:
        sentiment_col = 'тональность' if 'тональность' in df.columns else 'sentiment'
        fig = DataVisualizer.sentiment_distribution(df, sentiment_col)
        st.subheader("Распределение тональности")
        DataVisualizer.display_in_streamlit(fig)
    
    # Проверяем, есть ли в результатах ключевые слова
    if 'ключевые_слова' in df.columns or 'keywords' in df.columns:
        keyword_col = 'ключевые_слова' if 'ключевые_слова' in df.columns else 'keywords'
        fig = DataVisualizer.keyword_frequency(df, keyword_col)
        st.subheader("Частота ключевых слов/фраз")
        DataVisualizer.display_in_streamlit(fig)
    
    # Если есть дата и числовая метрика, показываем временной ряд
    date_cols = [col for col in df.columns if df[col].dtype == 'datetime64[ns]' or 'дата' in col.lower() or 'date' in col.lower()]
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if date_cols and numeric_cols:
        st.subheader("Анализ изменений во времени")
        date_col = st.selectbox("Выберите столбец с датой", date_cols)
        metric_col = st.selectbox("Выберите метрику", numeric_cols)
        
        fig = DataVisualizer.time_series_analysis(df, date_col, metric_col)
        DataVisualizer.display_in_streamlit(fig)