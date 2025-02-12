import streamlit as st
import pandas as pd
import time
from io import BytesIO
import json
from openai import OpenAI  # Или ваша библиотека для DeepSeek

def main():
    st.title("Обработка Excel через DeepSeek LLM (с повторными попытками)")
    
    if "processing" not in st.session_state:
        st.session_state["processing"] = False
    if "logs" not in st.session_state:
        st.session_state["logs"] = []

    # Ввод API Key и т.д.
    api_key = st.text_input("DeepSeek API Key", type="password")
    base_url = "https://api.deepseek.com"
    
    st.subheader("Настройки модели")
    model = st.text_input("Модель", value="deepseek-chat")
    temperature = st.number_input("Temperature", value=0.7, min_value=0.0, max_value=2.0, step=0.1)
    max_tokens = st.number_input("Max Tokens", value=300, min_value=1, max_value=4000, step=50)
    top_p = st.number_input("Top P", value=1.0, min_value=0.0, max_value=1.0, step=0.1)
    frequency_penalty = st.number_input("Frequency Penalty", value=0.0, min_value=0.0, max_value=2.0, step=0.1)
    presence_penalty = st.number_input("Presence Penalty", value=0.0, min_value=0.0, max_value=2.0, step=0.1)
    
    st.write("---")

    uploaded_file = st.file_uploader("Загрузите Excel", type=["xlsx","xls"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Превью:", df.head())
        
        target_column = st.selectbox("Целевой столбец", df.columns)
        additional_columns = st.multiselect("Доп. столбцы", df.columns, default=[])
        prompt = st.text_area("Промпт (например, 'напиши красиво...')")

        if st.button("Обработать Excel", disabled=st.session_state["processing"]):
            st.session_state["processing"] = True
            st.session_state["logs"].clear()

            with st.spinner("Идёт обработка..."):
                if not api_key:
                    st.error("Введите корректный ключ API.")
                    st.session_state["processing"] = False
                    return

                client = OpenAI(api_key=api_key, base_url=base_url)
                result_col = f"{target_column}_LLM_Ответ"
                df[result_col] = ""

                for i, row in df.iterrows():
                    text_for_llm = str(row[target_column])

                    if additional_columns:
                        additional_context = [f"{col}: {row[col]}" for col in additional_columns]
                        additional_context_str = "\n".join(additional_context)
                    else:
                        additional_context_str = ""

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

                    # Лог запись - на случай, если будем делать несколько попыток
                    row_log = {
                        "row_index": i,
                        "attempts": []
                    }

                    max_retries = 3
                    attempt = 0
                    success = False
                    llm_answer = ""

                    while not success and attempt < max_retries:
                        attempt += 1
                        attempt_log = {
                            "attempt_number": attempt,
                            "messages": messages,
                            "raw_response": None,
                            "parsed_answer": None,
                            "error": None
                        }

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

                            attempt_log["raw_response"] = str(response)
                            
                            llm_answer = response.choices[0].message.content.strip()
                            attempt_log["parsed_answer"] = llm_answer
                            success = True  # мы получили корректный ответ
                        
                        except json.JSONDecodeError as jde:
                            attempt_log["error"] = f"JSONDecodeError: {jde}"
                            # Можно подождать пару секунд и повторить
                        
                        except Exception as e:
                            attempt_log["error"] = f"Ошибка при вызове API: {e}"
                            # Если это rate-limit или сеть, повтор тоже может помочь
                        
                        # Записываем попытку
                        row_log["attempts"].append(attempt_log)

                        if not success:
                            # Подождём пару секунд, вдруг поможет
                            time.sleep(2)

                    # Запись результата в DF (либо ошибку, либо успешный ответ)
                    if success:
                        df.at[i, result_col] = llm_answer
                    else:
                        # Если и после max_retries не получилось
                        df.at[i, result_col] = f"Не удалось получить ответ после {max_retries} попыток"
                    
                    # Добавляем лог по строке
                    st.session_state["logs"].append(row_log)

                    # Небольшая пауза после каждой строки (опционально)
                    time.sleep(1)

                st.success("Готово!")
                st.write(df.head())

                # Скачивание результата
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False)
                processed_data = output.getvalue()

                st.download_button(
                    label="Скачать результат Excel",
                    data=processed_data,
                    file_name="processed.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.session_state["processing"] = False
        
        # Кнопка скачать логи
        if st.session_state["logs"]:
            log_lines = []
            for row_log in st.session_state["logs"]:
                log_lines.append(f"=== Строка: {row_log['row_index']} ===")
                for att in row_log["attempts"]:
                    log_lines.append(f"Попытка {att['attempt_number']}")
                    log_lines.append(f"Messages: {att['messages']}")
                    log_lines.append(f"Raw response: {att['raw_response']}")
                    log_lines.append(f"Parsed answer: {att['parsed_answer']}")
                    log_lines.append(f"Error: {att['error']}")
                log_lines.append("")

            full_text = "\n".join(log_lines)
            st.download_button(
                label="Скачать логи (TXT)",
                data=full_text.encode("utf-8"),
                file_name="logs.txt",
                mime="text/plain"
            )

if __name__ == "__main__":
    main()

