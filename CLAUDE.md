# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the Application
```bash
# Start the Streamlit application
streamlit run app.py
```

### Testing
```bash
# Run all tests
python run_tests.py

# Run specific test module
python -m unittest tests.test_excel_handler
python -m unittest tests.test_api_utils
```

### Dependencies
```bash
# Install all requirements
pip install -r requirements.txt
```

## Architecture Overview

### Core Application Structure
This is a **Streamlit-based Business Intelligence platform** that uses LLMs (primarily DeepSeek) to analyze Excel data and generate insights. The architecture follows a modular design pattern with clear separation of concerns.

### Key Components

1. **Main Application (`app.py`)**
   - Entry point for the Streamlit application
   - Handles UI state management and page configuration
   - Orchestrates data processing flow between modules
   - Implements caching for Excel file operations

2. **LLM Integration Layer (`modules/`)**
   - `unified_llm_fixed.py` - Main unified interface for both local and cloud LLM providers
   - `llm_integration.py` - Cloud-based LLM service integration (DeepSeek API)
   - `local_llm_integration.py` - Local LLM support (Ollama)
   - `xinference_integration.py` - XInference platform integration
   - Supports provider switching between cloud and local models

3. **Data Processing Pipeline**
   - `modules/excel_handler.py` - Core Excel file processing and DataFrame operations
   - `modules/data_processor.py` - Data transformation and preprocessing logic
   - `modules/file_utils.py` - File I/O operations and context file handling
   - Supports both row-by-row and full-table analysis modes

4. **UI Components (`ui/`)**
   - `llm_settings_view.py` - LLM configuration interface
   - `visualization_view.py` - Data visualization components
   - `scheduler_view.py` - Task scheduling interface
   - `export_view.py` - Results export functionality

5. **Configuration Management (`utils/`)**
   - `profile_manager.py` - Saves and loads analysis profiles
   - `config_manager.py` - Application-wide configuration handling
   - Profile system allows saving API keys, prompts, and analysis settings

### Analysis Modes
The application supports three distinct analysis approaches:
- **Row-by-Row Analysis**: Processes each row individually with LLM
- **Full Table Analysis**: Analyzes entire dataset as context
- **Combined Analysis**: Executes both modes in sequence

### Key Integration Points
- **LLM Provider Selection**: Switch between cloud (DeepSeek) and local (Ollama/XInference) providers via `UnifiedLLM` class
- **Context Enhancement**: Upload supplementary files (.txt, .csv, .md) to provide additional context for analysis
- **Prompt Library**: Built-in business-focused prompts in `modules/prompt_library.py`
- **Retry Mechanism**: Robust error handling with automatic retries for API failures

### State Management
- Uses Streamlit's session state for managing UI state
- Caching implemented via `@st.cache_data` decorators for expensive operations
- Profile persistence through JSON configuration files

### Language Support
- Primary interface and comments in Russian
- Supports multilingual data analysis
- Uses `pymorphy2` for Russian morphological analysis
- `langdetect` for automatic language detection