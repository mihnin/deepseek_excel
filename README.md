# DeepSeek Excel Processor

Это веб-приложение позволяет обрабатывать файлы Excel с использованием LLM DeepSeek. Приложение загружает Excel файл, позволяет выбрать определённый столбец для отправки его содержимого в LLM (а также дополнительные столбцы для контекста), задаёт параметры модели (например, температуру, max tokens и другие) и после получения ответа от LLM добавляет результаты в новый столбец. Итоговый файл можно скачать для дальнейшего использования.

## Установка

### 1. Установка Python 3.10 и Anaconda/Miniconda

1. Скачайте и установите [Miniconda](https://docs.conda.io/en/latest/miniconda.html) или [Anaconda](https://www.anaconda.com/products/individual).

2. Создайте новое окружение с Python 3.10:

   ```bash
   conda create -n deepseek_excel python=3.10 -y
   conda activate deepseek_excel


```markdown
# DeepSeek Excel Processor

Это веб-приложение позволяет обрабатывать файлы Excel с использованием LLM DeepSeek. Приложение загружает Excel файл, позволяет выбрать определённый столбец для отправки его содержимого в LLM (а также дополнительные столбцы для контекста), задаёт параметры модели (например, температуру, max tokens и другие) и после получения ответа от LLM добавляет результаты в новый столбец. Итоговый файл можно скачать для дальнейшего использования.

## Установка

### 1. Установка Python 3.10 и Anaconda/Miniconda

1. Скачайте и установите [Miniconda](https://docs.conda.io/en/latest/miniconda.html) или [Anaconda](https://www.anaconda.com/products/individual).

2. Создайте новое окружение с Python 3.10:

   ```bash
   conda create -n deepseek_env python=3.10
   conda activate deepseek_env
   ```

### 2. Установка зависимостей

Перейдите в каталог проекта (например, deepseek_excel) и выполните команду:

```bash
pip install -r requirements.txt
```

## Запуск приложения

Для старта приложения выполните команду:

```bash
streamlit run app.py
```

После этого откроется веб-интерфейс приложения в браузере.

## Пример использования

1. **Ввод API Key:**  
   На стартовой странице введите ваш DeepSeek API Key в специальное поле (тип — пароль).

2. **Настройка параметров модели:**  
   Укажите модель (например, "deepseek-chat"), установите значения параметров, таких как Temperature, Max Tokens, Top P, Frequency Penalty и Presence Penalty.

3. **Загрузка Excel файла:**  
   Используйте кнопку «Загрузите ваш Excel файл», чтобы выбрать файл с расширениями XLSX или XLS. После загрузки отобразится превью DataFrame.

4. **Выбор столбцов:**  
   Выберите столбец, данные которого будут отправлены в LLM, и по желанию дополнительные столбцы, которые добавят контекст к запросу.

5. **Ввод промпта:**  
   В поле ввода промпта укажите текст запроса для LLM. Пример:  
   "Сделай краткое содержание"  
   Этот промпт объединяется с текстом выбранного столбца и дополнительными данными из других столбцов.

6. **Обработка:**  
   После нажатия на кнопку «Обработать Excel» приложение пройдёт по каждой строке выбранного столбца, отправит запрос к LLM и запишет результат в новый столбец (название которого формируется на основе исходного столбца).

7. **Скачивание результата:**  
   После завершения обработки отобразится обновлённый DataFrame и появится кнопка для скачивания результирующего Excel файла.

## Структура проекта

- **app.py** – основной скрипт Streamlit приложения, реализующий логику загрузки, обработки и скачивания данных.
- **requirements.txt** – список необходимых библиотек:
  - streamlit
  - pandas
  - openpyxl
  - openai

## Замечания

- Для корректной работы приложения необходимо наличие активного интернет-соединения, так как для обработки используется запрос к API DeepSeek.
- Убедитесь, что ваш API Key корректен и имеет необходимые права.
- При возникновении ошибок проверьте настройки модели и параметры запроса.

---
Данный проект предназначен для упрощения обработки Excel данных и интеграции возможностей LLM для анализа и преобразования табличных данных.
```
