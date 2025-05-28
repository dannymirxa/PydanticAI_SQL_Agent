# PydanticAI SQLite Agent Documentation

## 1. Project Overview

The PydanticAI SQLite Agent is a Python application that leverages a Large Language Model (LLM), specifically Google's Gemini, to interact with an SQLite database. Users can ask questions in natural language, and the agent will use a set of defined tools to understand the database structure, construct appropriate SQL queries, execute them, and return the results. This project showcases the use of Pydantic AI for building robust AI agents, SQLAlchemy for database interaction, and `python-dotenv` for configuration management.

## 2. Project Structure

The project is organized into the following key Python files:

- `PydanticAI_SQLite_Agent/sql.py`: Provides low-level functions for database operations like listing tables, describing table schemas, and running SQL queries.
- `PydanticAI_SQLite_Agent/load_models.py`: Handles the configuration and instantiation of the Gemini language model.
- `PydanticAI_SQLite_Agent/sql_agent.py`: Defines the core AI agent, its tools (which wrap functions from `sql.py`), system prompt, and the main execution logic for user interaction.
- `PydanticAI_SQLite_Agent/.env`: (User-created) Stores sensitive information like API keys.
- `PydanticAI_SQLite_Agent/.gitignore`: Specifies intentionally untracked files that Git should ignore.

## 3. Core Components

### 3.1. `PydanticAI_SQLite_Agent/sql.py` - Database Interaction Utilities

This module is responsible for all direct interactions with the SQLite database using SQLAlchemy. It abstracts the database operations into reusable functions.

- **`list_tables(db_engine: Engine) -> str`**
    - **Purpose**: Retrieves a list of all table names from the connected database.
    - **Arguments**:
    - `db_engine (Engine)`: The SQLAlchemy engine instance.
    - **Returns**: A JSON string representing a list of table names (e.g., `["Album", "Artist", "Customer"]`). Returns an error message string on failure.

- **`describe_table(db_engine: Engine, table_name: str) -> str`**
    - **Purpose**: Fetches the schema (column names, types, etc.) for a specified table.
    - **Arguments**:
        - `db_engine (Engine)`: The SQLAlchemy engine instance.
        - `table_name (str)`: The name of the table to describe.
    - **Returns**: A JSON string representing a list of column descriptions for the table. Each column description is a string representation of a SQLAlchemy `Column` object (e.g., `["{'name': 'AlbumId', 'type': INTEGER(), ...}", ...]`). Returns an error message string on failure.

- **`run_sql_query(db_engine: Engine, query: str, limit: Optional[int] = 10) -> str`**
    - **Purpose**: Executes a given SQL query against the database.
    - **Arguments**:
        - `db_engine (Engine)`: The SQLAlchemy engine instance.
        - `query (str)`: The SQL query to execute.
        - `limit (Optional[int])`: The maximum number of rows to return (defaults to 10). If `None`, all rows are returned.
    - **Returns**: A JSON string representing a list of dictionaries, where each dictionary is a row from the query result. Dates and other non-standard JSON types are converted to strings. Returns an error message string if an exception occurs during query execution or result processing.

### 3.2. `PydanticAI_SQLite_Agent/load_models.py` - Language Model Configuration

This script is dedicated to setting up the language model used by the AI agent.

- **Functionality**:
    -   Loads environment variables from a `.env` file using `dotenv`.
    -   Retrieves the `GEMINI_API_KEY` from the environment variables.
    -   Initializes a `GeminiModel` instance from `pydantic_ai.models.gemini`.
        -   Model specified: `'gemini-2.0-flash'`.
        -   Provider: `GoogleGLAProvider` configured with the `GEMINI_API_KEY`.
- **Output**:
    - `GEMINI_MODEL`: A configured instance of `GeminiModel` that is imported and used by `sql_agent.py`.

### 3.3. `PydanticAI_SQLite_Agent/sql_agent.py` - The AI Agent

This is the central script where the AI agent is defined, configured, and run.

- **System Prompt**:
    -   A detailed instruction set for the LLM, guiding its behavior. It mandates a specific workflow:
        1.  Use `list_tables_tool` to get a list of tables.
        2.  Use `describe_table_tool` to understand the schema of relevant tables.
        3.  Construct the SQL query and execute it using `run_sql_tool`.
    -   It also requests the agent to return the entire result.

- **`Dependencies` Dataclass**:
    - `@dataclass class Dependencies:`
        - `db_engine: Engine`
    -   A simple container to pass shared resources (like the database engine) to the agent's tools via the `RunContext`.

- **`ResponseModel` (Pydantic Model)**:
    - `class ResponseModel(BaseModel):`
        - `detail: str = Field(alias='Detail', description='The result of the query. ')`
    -   Defines the expected JSON structure for the agent's final output, ensuring consistency. The LLM's response will be parsed into this model.

- **Agent Initialization**:
    - `agent = Agent(...)`
    -   An instance of `pydantic_ai.Agent` is created with:
        - `name`: 'SQLite Agent'
        - `model`: The `GEMINI_MODEL` imported from `load_models.py`.
        - `system_prompt`: The multi-step instruction defined earlier.
        - `output_type`: The `ResponseModel` to structure the output.

- **Agent Tools**:
    -   Functions decorated with `@agent.tool` become available for the LLM to call. These tools wrap the database utility functions from `sql.py`.
    - **`list_tables_tool(ctx: RunContext) -> str`**:
        -   Calls `sql.list_tables` using `ctx.deps.db_engine`.
    - **`describe_table_tool(ctx: RunContext, table_name: str) -> str`**:
        -   Calls `sql.describe_table` using `ctx.deps.db_engine` and the `table_name` provided by the LLM.
    - **`run_sql_tool(ctx: RunContext, query: str, limit: int = 10) -> str`**:
        -   Calls `sql.run_sql_query` using `ctx.deps.db_engine`, the `query` generated by the LLM, and an optional `limit`.

- **Main Execution Block (`if __name__ == "__main__":`)**:
    -   Creates a SQLAlchemy engine for an SQLite database (e.g., `sqlite:///./Chinook_Sqlite.sqlite`).
    -   Instantiates `Dependencies` with the engine.
    -   Demonstrates how to run the agent synchronously using `agent.run_sync()`:
        -   An initial query ("How many tables are there?").
        -   A follow-up query ("in ASCII, illustrate the relation of each of them") showcasing the use of `message_history` to maintain conversation context.
    -   Prints the `detail` field from the agent's structured output.

## 4. Setup and Installation

1.  **Prerequisites**:
    -   Python 3.x
    -   Access to Google Gemini API.

2.  **Clone the Repository** (if applicable):
    ```bash
    git clone <repository-url>
    cd PydanticAI_SQLite_Agent
    ```

3.  **Install Dependencies**:
    It's recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install pydantic-ai sqlalchemy python-dotenv google-generativeai
    ```

4.  **Create `.env` File**:
    In the root directory of the project (`PydanticAI_SQLite_Agent/`), create a file named `.env` and add your Gemini API key:
    ```env
    GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
    ```
    This file is listed in `.gitignore` and should not be committed to version control.

5.  **SQLite Database**:
    -   The example in `sql_agent.py` uses a SQLite database file named `Chinook_Sqlite.sqlite`.
    -   Place this file (or your desired SQLite database file) in the root directory of the project.
    -   If you use a different database file or path, update the `create_engine` call in `sql_agent.py`:
        ```python
        # In sql_agent.py
        db_engine = create_engine('sqlite:///./Your_Database_Name.sqlite')
        ```

## 5. Usage

To run the AI agent, execute the `sql_agent.py` script from the project's root directory:

```bash
python ./PydanticAI_SQLite_Agent/sql_agent.py
