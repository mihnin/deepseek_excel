import streamlit as st
import pandas as pd
from io import BytesIO
from openai import OpenAI  # Предполагаем, что это совместимый клиент с DeepSeek

def main():
    st.title("Обработка Excel через DeepSeek LLM")

    # 1. Ввод API Key
    api_key = st.text_input("Введите ваш DeepSeek API Key", type="password")
    base_url = "https://api.deepseek.com"

    # 2. Параметры модели
    st.subheader("Настройка параметров модели")
    model = st.text_input("Модель", value="deepseek-chat")
    temperature = st.number_input("Temperature", value=0.7, min_value=0.0, max_value=2.0, step=0.1)
    max_tokens = st.number_input("Max Tokens", value=300, min_value=1, max_value=4000, step=50)
    top_p = st.number_input("Top P", value=1.0, min_value=0.0, max_value=1.0, step=0.1)
    frequency_penalty = st.number_input("Frequency Penalty", value=0.0, min_value=0.0, max_value=2.0, step=0.1)
    presence_penalty = st.number_input("Presence Penalty", value=0.0, min_value=0.0, max_value=2.0, step=0.1)

    st.write("---")

    # 3. Загрузка Excel
    uploaded_file = st.file_uploader("Загрузите ваш Excel файл", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Превью загруженного DataFrame:", df.head())

        # Выбор столбца для обработки
        target_column = st.selectbox("Выберите столбец, который нужно отправлять в LLM", df.columns)
        
        # Выбор дополнительных столбцов
        additional_columns = st.multiselect("Выберите дополнительные столбцы, которые следует учитывать в промпте", df.columns, default=[])

        # Ввод промпта
        prompt = st.text_area("Введите промпт для LLM (например, 'Сделай саммари')")

        # 4. Кнопка обработки
        if st.button("Обработать Excel"):
            # Инициализируем клиента DeepSeek (совместимый с OpenAI)
            client = None
            if api_key:
                client = OpenAI(api_key=api_key, base_url=base_url)
            else:
                st.error("Пожалуйста, введите корректный API Key.")
                return

            # Новый столбец для результата
            result_column_name = f"{target_column}_LLM_Ответ"
            df[result_column_name] = ""

            # Пройдёмся по каждой строке целевого столбца
            for i, row in df.iterrows():
                text_for_llm = str(row[target_column])

                # Формируем контекст из дополнительных столбцов
                if additional_columns:
                    additional_context = []
                    for col in additional_columns:
                        additional_context.append(f"{col}: {row[col]}")
                    additional_context_str = "\n".join(additional_context)
                else:
                    additional_context_str = ""

                # Формируем сообщение
                # Например, система задаёт роль ассистента, а пользовательский промпт включает текст ячейки + контекст.
                messages = [
                    {"role": "system", "content": "Вы – полезный ассистент."},
                    {
                        "role": "user",
                        "content": (
                            f"{prompt}\n\n"
                            f"Текст целевого столбца: {text_for_llm}\n\n"
                            f"Дополнительные данные:\n{additional_context_str}"
                        )
                    }
                ]

                try:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        frequency_penalty=frequency_penalty,
                        presence_penalty=presence_penalty,
                        stream=False
                    )
                    llm_answer = response.choices[0].message.content.strip()
                except Exception as e:
                    llm_answer = f"Ошибка при вызове API: {str(e)}"

                # Запишем результат в новый столбец
                df.at[i, result_column_name] = llm_answer
            
            st.success("Обработка завершена!")
            st.write(df.head())

            # 5. Скачивание результата
            # Сохраним DataFrame в байтовый буфер в формате Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            processed_data = output.getvalue()

            st.download_button(
                label="Скачать результат Excel",
                data=processed_data,
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
