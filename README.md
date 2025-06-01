# PydanticAI SQLite Agent: Simple Documentation

## What is this?

The PydanticAI SQLite Agent is a Python application that lets you "talk" to your SQLite database using everyday language. It uses Google's Gemini (a Large Language Model) to understand your questions, figure out the right SQL query, run it, and give you back the answer.

Think of it as a smart assistant for your database!

## Key Features

*   **Natural Language Queries**: Ask questions like "How many customers are there?" instead of writing complex SQL.
*   **Smart Tool Usage**: The agent automatically uses tools to:
    *   See what tables are in your database.
    *   Understand the structure (columns, data types) of those tables.
    *   Build and run the correct SQL query.
*   **Structured Output**: Get results in a clean, predictable JSON format.
*   **Easy Configuration**: Uses a `.env` file for your API keys.

## Core Components

The project is mainly built around these Python files:

*   `sql.py`: Handles all the direct database stuff – listing tables, describing them, and running SQL queries.
*   `load_models.py`: Sets up the Google Gemini language model.
*   `sql_agent.py`: This is the brain! It defines the AI agent, its tools (which use `sql.py`), and how it should behave. It also includes the main script to run the agent.

## Quick Setup

1.  **Get the Code**:
    If you haven't already, clone the repository:
    ```bash
    git clone <repository-url>
    cd PydanticAI_SQLite_Agent
    ```

2.  **Install Necessary Packages**:
    It's best to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install pydantic-ai sqlalchemy python-dotenv google-generativeai
    ```

3.  **Set Up Your API Key**:
    *   Create a file named `.env` in the `PydanticAI_SQLite_Agent/` directory.
    *   Add your Google Gemini API key to it like this:
        ```env
        GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
        ```
    *   (This file is ignored by Git, so your key stays private).

4.  **Get Your SQLite Database Ready**:
    *   The example uses a database file named `Chinook_Sqlite.sqlite`.
    *   Place this file (or your own SQLite database) in the main project directory (`PydanticAI_SQLite_Agent/`).
    *   If you use a different database name, you'll need to update it in `sql_agent.py`:
        ```python
        # In PydanticAI_SQLite_Agent/sql_agent.py
        db_engine = create_engine('sqlite:///./Your_Database_Name.sqlite')
        ```

## How to Use

Once everything is set up, run the agent from your terminal (make sure you're in the project's root directory):

```bash
python ./PydanticAI_SQLite_Agent/sql_agent.py
