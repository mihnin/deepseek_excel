# modules/visualization.py

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

class DataVisualizer:
    @staticmethod
    def sentiment_distribution(df, sentiment_column):
        """Визуализирует распределение тональности в отзывах/текстах"""
        # Подсчет количества отзывов по категориям
        sentiment_counts = df[sentiment_column].value_counts().reset_index()
        sentiment_counts.columns = ['Тональность', 'Количество']
        
        # Создание круговой диаграммы
        fig = px.pie(
            sentiment_counts, 
            values='Количество', 
            names='Тональность',
            title='Распределение тональности',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        return fig
    
    @staticmethod
    def keyword_frequency(data, keyword_column, top_n=20):
        """Визуализирует частоту ключевых слов/фраз"""
        # Объединяем все ключевые слова в один список
        all_keywords = []
        for keywords in data[keyword_column]:
            if isinstance(keywords, str):
                # Предполагаем, что ключевые слова разделены запятыми
                keywords_list = [k.strip() for k in keywords.split(',')]
                all_keywords.extend(keywords_list)
        
        # Подсчет частоты
        keyword_freq = pd.Series(all_keywords).value_counts().reset_index()
        keyword_freq.columns = ['Ключевое слово', 'Частота']
        
        # Выбираем top_n наиболее частых
        keyword_freq = keyword_freq.head(top_n)
        
        # Создание горизонтальной столбчатой диаграммы
        fig = px.bar(
            keyword_freq,
            x='Частота',
            y='Ключевое слово',
            orientation='h',
            title=f'Топ-{top_n} ключевых слов/фраз',
            color='Частота',
            color_continuous_scale='Viridis'
        )
        
        return fig
    
    @staticmethod
    def time_series_analysis(df, date_column, metric_column, title="Временной ряд"):
        """Визуализирует изменение метрики во времени"""
        # Убедимся, что дата в правильном формате
        if df[date_column].dtype != 'datetime64[ns]':
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # Сортировка по дате
        df_sorted = df.sort_values(by=date_column)
        
        # Создание графика
        fig = px.line(
            df_sorted, 
            x=date_column, 
            y=metric_column,
            title=title,
            labels={date_column: 'Дата', metric_column: 'Значение'},
            line_shape='linear'
        )
        
        return fig
    
    @staticmethod
    def display_in_streamlit(fig, use_container_width=True):
        """Отображает фигуру Plotly в интерфейсе Streamlit"""
        st.plotly_chart(fig, use_container_width=use_container_width)