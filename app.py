import streamlit as st
import pandas as pd
import time
from io import BytesIO
import json
from openai import OpenAI  # Или ваша библиотека для DeepSeek

def main():
    st.title("Обработка Excel через DeepSeek LLM (с повторными попытками)")
    
    # Инициализация переменных в session_state
    if "processing" not in st.session_state:
        st.session_state["processing"] = False
    if "logs" not in st.session_state:
        st.session_state["logs"] = []

    # Ввод API Key и базового URL
    api_key = st.text_input("DeepSeek API Key", type="password")
    base_url = "https://api.deepseek.com"
    
    # Настройки модели
    st.subheader("Настройки модели")
    model = st.text_input("Модель", value="deepseek-chat")
    temperature = st.number_input("Temperature", value=0.7, min_value=0.0, max_value=2.0, step=0.1)
    max_tokens = st.number_input("Max Tokens", value=300, min_value=1, max_value=4000, step=50)
    top_p = st.number_input("Top P", value=1.0, min_value=0.0, max_value=1.0, step=0.1)
    frequency_penalty = st.number_input("Frequency Penalty", value=0.0, min_value=0.0, max_value=2.0, step=0.1)
    presence_penalty = st.number_input("Presence Penalty", value=0.0, min_value=0.0, max_value=2.0, step=0.1)
    
    st.write("---")

    # Загрузка Excel файла
    uploaded_file = st.file_uploader("Загрузите Excel", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {e}")
            return
        
        st.write("Превью:", df.head())
        target_column = st.selectbox("Целевой столбец", df.columns)
        additional_columns = st.multiselect("Доп. столбцы", df.columns, default=[])
        prompt = st.text_area("Промпт (например, 'напиши красиво...')")
        
        if st.button("Обработать Excel", disabled=st.session_state["processing"]):
            st.session_state["processing"] = True
            st.session_state["logs"].clear()

            try:
                with st.spinner("Идёт обработка..."):
                    if not api_key:
                        st.error("Введите корректный ключ API.")
                        return

                    client = OpenAI(api_key=api_key, base_url=base_url)
                    result_col = f"{target_column}_LLM_Ответ"
                    df[result_col] = ""

                    # Обработка каждой строки Excel
                    for i, row in df.iterrows():
                        text_for_llm = str(row[target_column])
                        additional_context_str = ""
                        if additional_columns:
                            additional_context = [f"{col}: {row[col]}" for col in additional_columns]
                            additional_context_str = "\n".join(additional_context)

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

                        # Логирование попыток для данной строки
                        row_log = {"row_index": i, "attempts": []}
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
                                
                                # Получение и обработка ответа от LLM
                                llm_answer = response.choices[0].message.content.strip()
                                attempt_log["parsed_answer"] = llm_answer
                                success = True
                            
                            except json.JSONDecodeError as jde:
                                attempt_log["error"] = f"JSONDecodeError: {jde}"
                            
                            except Exception as e:
                                attempt_log["error"] = f"Ошибка при вызове API: {e}"
                            
                            # Добавляем лог по данной попытке
                            row_log["attempts"].append(attempt_log)

                            if not success:
                                time.sleep(2)  # Небольшая задержка перед повторной попыткой

                        # Записываем результат в DataFrame
                        if success:
                            df.at[i, result_col] = llm_answer
                        else:
                            df.at[i, result_col] = f"Не удалось получить ответ после {max_retries} попыток"
                        
                        st.session_state["logs"].append(row_log)
                        time.sleep(1)  # Пауза между обработкой строк

                st.success("Готово!")
                st.write(df.head())

                # Подготовка Excel для скачивания
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

            finally:
                # Гарантированный сброс флага обработки
                st.session_state["processing"] = False
        
        # Кнопка для скачивания логов
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
