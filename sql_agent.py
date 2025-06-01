from textwrap import dedent
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import Engine, create_engine
from load_models import OPENAI_MODEL
from sql_operations import list_tables, describe_table, run_sql_query
from dataframe import create_dataframe_pl
from typing import Annotated
from annotated_types import MinLen
from typing_extensions import TypeAlias, Union
import json

system_prompt = dedent("""
    You an AI agent are equipped with SQLite tools. Your goal is to help users interact with a SQLite database.

    To run a SQL, follow the steps:
    1. first, run the `list_tables` tool to get a list of tables in the database.
    2. then, run the `describe_table` tool to get a description of the target tables in the database.
    3. finally, construct the SQL statement and run the `run_sql` tool to run the SQL query on the database.

    When returning the results, please return the entire result
""")

@dataclass
class Dependencies:
    db_engine: Engine

class Success(BaseModel):
    sql_query: Annotated[str, MinLen(1)]
    # explanation: str = Field("", description="Explanation of the SQL query, as markdown")
    detail: str = Field(alias='Detail', description='Explanation of the SQL query and the result of the query, as markdown')

class InvalidRequest(BaseModel):
    error_message: str

Response: TypeAlias = Union[Success, InvalidRequest]

# class ResponseModel(BaseModel):
#     detail: str = Field(alias='Detail', description='The result of the query. ')

agent = Agent(
        name='SQLite Agent',
        model=OPENAI_MODEL,
        # system_prompt=[system_prompt],
        output_type=Response
)

@agent.system_prompt
async def system_prompt() -> str:
    return f"""\
    You are an AI agent equipped with SQLite tools. Your goal is to help users interact with a SQLite database by generating and executing SQL queries.

    Follow these steps meticulously:
    1.  **List Tables:** If you need to know the available tables, use the `list_tables_tool`.
    2.  **Describe Table:** To understand the schema of specific table(s) relevant to the user's request, use the `describe_table_tool` for each of them.
    3.  **Run SQL Query:** Construct the SQL query based on the user's request and the table schemas. Execute it using the `run_sql_tool`. This tool will return a JSON string of the query results (or an error/empty array if no data).
    4.  **Process SQL Result & Create DataFrame:**
        a.  Examine the JSON string output from `run_sql_tool`.
        b.  If the output indicates that data was successfully returned (e.g., it's a non-empty JSON array like `[{{\"column\": \"value\"}}]` and not an error structure like `{{ \"error\": ... }}` or an empty array `[]`), then you MUST proceed to call the `create_dataframe_tool`.
        c.  Call `create_dataframe_tool` with the EXACT SAME SQL query you used in `run_sql_tool`.
        d.  The JSON string returned by `create_dataframe_tool` is the definitive data result.
    5.  **Formulate Response:** Construct your final response. If the query was successful and data was processed by `create_dataframe_tool`, include the SQL query and the data from `create_dataframe_tool` in the 'detail' field of your `Success` response. If at any stage an error occurs or a query yields no data (after `run_sql_tool`), explain this in the `detail` field or use an `InvalidRequest` response if appropriate.
    
    When returning the results in the `Success` object, the `detail` field should be formatted as markdown and comprehensively contain:
    - An explanation of the SQL query and the steps taken.
    - The SQL query that was executed.
    - If data was successfully retrieved and processed by `create_dataframe_tool`, include the complete JSON string result. This JSON string should be presented clearly within a JSON markdown code block. For example:
      ```json
      [{{\"column_name1\": \"value1\", \"column_name2\": \"value2\"}}]
      ```
    If no data was returned by the query or if an error occurred at any step, this should be clearly explained in the `detail` field.
    """

@agent.tool
def list_tables_tool(ctx: RunContext[Dependencies]) -> str:
    print('list_tables_tool called')
    """Use this function to get a list of table names in the database. """
    return list_tables(ctx.deps.db_engine)

@agent.tool
def describe_table_tool(ctx: RunContext[Dependencies], table_name: str) -> str:
    print('describe_table_tool called', table_name)
    """Use this function to get a description of a table in the database."""
    return describe_table(ctx.deps.db_engine, table_name)

@agent.tool
def run_sql_tool(ctx: RunContext[Dependencies], query: str, limit: int = 10) -> str:
    print('run_sql_tool called', query)
    """Use this function to run a SQL query on the database. """
    return run_sql_query(ctx.deps.db_engine, query, limit)

@agent.tool
def create_dataframe_tool(ctx: RunContext[Dependencies], query: str) -> str:
    print('create_dataframe_tool called with query:', query)
    """\
    Use this function ONLY AFTER 'run_sql_tool' has confirmed that a query returns data.
    This tool takes the same SQL query that was run by 'run_sql_tool'.
    It re-executes the query to generate a JSON string representation of the complete result set.
    This JSON string is intended for the final presentation of query results to the user.
    Do not call this if 'run_sql_tool' indicated no data or an error.
    """
    return create_dataframe_pl(ctx.deps.db_engine, query)

@agent.output_validator
def response_output_validator(output: Response) -> Response:
    """
    Custom validator for the agent's output.
    Ensures that 'detail' in Success and 'error_message' in InvalidRequest are not empty.
    """
    if isinstance(output, Success):
        # The 'sql_query' field is already validated by Pydantic's MinLen(1)
        if not output.detail or not output.detail.strip():
            raise ValueError("Success response must include a non-empty 'detail' field.")
    elif isinstance(output, InvalidRequest):
        if not output.error_message or not output.error_message.strip():
            raise ValueError("InvalidRequest response must include a non-empty 'error_message'.")
    return output


if __name__=="__main__":
    # db_engine = create_engine('sqlite:///./Chinook_Sqlite.sqlite')
    db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')
    deps = Dependencies(db_engine=db_engine)

    response1 = agent.run_sync('How many tables are there?', deps=deps)
    print(response1.output.detail)

    response2 = agent.run_sync('List the artists with tracks consist of metal song and the number of their albums', 
                               deps=deps,
                               message_history=response1.new_messages()
                               )
    print(response2.output.detail)