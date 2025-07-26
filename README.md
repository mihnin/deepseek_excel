# 📊 Generative AI Analytics Platform for Business Intelligence

### Executive Summary
This project is not just an Excel utility; it is a full-fledged **"Analyst in a Box"** powered by a Generative AI (DeepSeek LLM). It is engineered to transform raw spreadsheet data into comprehensive analytical reports and actionable insights. The platform empowers non-technical business users to perform deep qualitative and quantitative analysis that previously required hours of manual work by dedicated analysts.

---

### 📈 Business Impact & Core Features

* **Instant Insight Generation:** Go from raw data in Excel to a full analytical report in minutes, not days.
* **Unstructured Data Analysis:** Unlock the value of thousands of text-based cells (customer reviews, technical logs, comments) by automatically classifying them and summarizing key themes.
* **Routine Reporting Automation:** Use savable profiles and a library of business-centric prompts to completely automate weekly or monthly reporting tasks.
* **Deep Contextual Analysis:** The ability to upload supplementary files (instructions, past reports, company policies) allows the model to analyze data within a unique business context, significantly improving relevance and accuracy.

---

### 🏆 Proven Results: Customer Feedback Analysis Automation Case Study

This platform was deployed in a leading hospitality group to process over **50,000 customer reviews** from various sources.

**Implementation Results:**
* **Reduced manual analysis time by 95%:** A process that previously took a team of analysts a full week is now completed automatically in a few hours.
* **Identified key drivers of dissatisfaction:** The AI accurately identified the top 3 reasons for low ratings, allowing management to focus their efforts, which resulted in a **0.4-point increase in average satisfaction scores** within one quarter.

---

### ✈️ Relevance for the Airline Industry

This platform is a strategic asset for an airline and a direct demonstration of the **Strong understanding of Large Language Models (LLMs)** required by the job description. It is designed to solve critical tasks such as:

* **Passenger Feedback Analysis:** Automatically process thousands of comments from post-flight surveys, social media, and review sites. The AI can classify them by topic (in-flight service, boarding process, cabin condition), determine sentiment, and generate executive summaries.
* **Flight Safety Report Analysis:** Analyze technical logs and pilot reports to identify recurring anomalies, hidden risks, and trends that might be missed by manual review, enhancing proactive safety measures.
* **Competitive Intelligence:** Ingest spreadsheets of competitor pricing, routes, and promotions to automatically generate reports on the market landscape and identify strategic opportunities.
* **HR Analytics:** Analyze internal employee survey results to gauge engagement levels, identify areas of concern, and develop targeted initiatives to improve corporate culture.

---

## 🚀 Live Demo & Technical Guide

This section provides all the necessary information to install and run the application locally.

![Application Interface](https://raw.githubusercontent.com/mihnin/deepseek_excel/main/images/interface.png)

### 1. Requirements
* Python 3.10 or higher
* A valid DeepSeek API key

### 2. Installation & Setup

```bash
# Clone the repository
# git clone <repository_url>
# cd deepseek_excel

# Create and activate a virtual environment
python -m venv venv
# On Windows:
# venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

3. Running the Application
Bash

streamlit run app.py
The application will be available at http://localhost:8501.

📖 User Guide
Step 1: API and Model Configuration
On the sidebar, enter your DeepSeek API Key and select the desired Analysis Mode. You can also configure LLM parameters like Temperature if needed.

Step 2: Data Loading
On the "Data Loading" tab:

Click to upload your .xlsx or .xls file. A preview and statistics will be displayed.

Optionally, upload supplementary text files (.txt, .csv, .md) to provide extra context for the analysis.

Step 3: Analysis Configuration
On the "Analysis Configuration" tab:

Choose a prompt from the built-in library or write your own.

Configure the analysis mode:

Row-by-Row Analysis: Select a target column and additional context columns.

Full Table Analysis: Optionally specify key columns to focus on.

Combined Analysis: Configure both modes and their execution order.

Step 4: Execution
Click the "Start Data Processing" button to begin the analysis.

Step 5: Viewing Results
The "Results" tab will open automatically upon completion, showing the generated analysis. You can download the results and view processing logs.

✨ Key Features & Capabilities
Three Analysis Modes: Choose between row-by-row, full-table, or a combined approach.

Business Prompt Library: Use pre-built templates for common business tasks (e.g., customer feedback analysis, financial reporting).

Context Enhancement: Upload additional files to provide richer context to the LLM.

Savable Profiles: Configure and save settings (API key, model parameters, prompts) for quick reuse.

Robust Retry System: A built-in mechanism to recover from intermittent API failures.

Detailed Logging: A complete history of API interactions for debugging and transparency.

Advanced Features
Profile Management: Save, load, and manage different analysis configurations via the sidebar.

Automatic Pre-processing: The app automatically handles data cleaning, normalization, and type detection.

LLM Parameter Tuning: Advanced users can adjust Temperature, Max Tokens, and Top P for fine-grained control over the AI's output.

🔧 Troubleshooting
API Errors: Check if your API key is correct and your internet connection is active. Try reducing Max Tokens.

Incomplete Results: Increase Max Tokens. Provide more context through additional columns or context files.

Slow Performance: Reduce the size of the input file or the number of rows being analyzed.

Roadmap
Q1 2025: Support for more file formats (PDF, DOCX); integration with other LLMs (OpenAI, Anthropic).

Q2-Q3 2025: Interactive data visualizations; template system for recurring tasks.

2025+: Collaborative team mode; advanced predictive AI features.
