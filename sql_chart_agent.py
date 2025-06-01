import pandas as pd
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import Engine, create_engine
from load_models import OPENAI_MODEL
from sql_operations import list_tables, describe_table, run_sql_query
from dataframe import create_dataframe_pd
from typing import Annotated
from annotated_types import MinLen
from typing_extensions import TypeAlias, Union, Optional
import json
import io
import re

@dataclass
class Dependencies:
    db_engine: Engine
    dataframe: pd.DataFrame = None

class SQLSuccess(BaseModel):
    sql_query: Annotated[str, MinLen(1)]
    detail: str = Field(alias='Detail', description='Explanation of the SQL query, steps taken, the result of the query (JSON), and chart generation summary if applicable, as markdown')
    chart_insights: Optional[Annotated[str, MinLen(1)]] = Field(None, description="Insights from the dataset and graph, if a chart was generated.")
    chart_python_code: Optional[Annotated[str, MinLen(1)]] = Field(None, description='Python code to plot the graph, as markdown, if a chart was generated.')

class InvalidRequest(BaseModel):
    error_message: str

SQLResponse: TypeAlias = Union[SQLSuccess, InvalidRequest]

class ChartResponses(BaseModel):
    insights: Annotated[str, MinLen(1), Field(alias='insights', description="insights from the dataset and graph")]
    python_code: Annotated[str, MinLen(1), Field(alias='python_code',description='Python code to plot the graph, as markdown')]

SQLAgent = Agent(
            name='SQL Query Agent',
            model=OPENAI_MODEL,
            output_type=SQLResponse
            )

chartAgent = Agent(
            name='Chart Generation Agent',
            model=OPENAI_MODEL,
            output_type=ChartResponses
            )

chartOptions = ('Scatter', 'Line', 'Histograph', 'Bargraph', 'Pie Chart')

@SQLAgent.system_prompt
async def system_prompt() -> str:
    return f"""\
    You are an AI agent equipped with database tools. Your goal is to help users interact with a database by generating and executing SQL queries, and if requested, facilitate chart generation.

    Follow these steps meticulously:
    1.  **List Tables:** If you need to know the available tables, use the `list_tables_tool`.
    2.  **Describe Table:** To understand the schema of specific table(s) relevant to the user's request, use the `describe_table_tool` for each of them.
    3.  **Run SQL Query:** Construct the SQL query based on the user's request and the table schemas. Execute it using the `run_sql_tool`. This tool will return a JSON string of the query results (or an error/empty array if no data).
    4.  **Process SQL Result & Create DataFrame:**
        a.  Examine the JSON string output from `run_sql_tool`.
        b.  If the output indicates that data was successfully returned (e.g., it's a non-empty JSON array like `[{{\"column\": \"value\"}}]` and not an error structure like `{{ \"error\": ... }}` or an empty array `[]`), then you MUST proceed to call the `create_dataframe_tool`.
        c.  Call `create_dataframe_tool` with the EXACT SAME SQL query you used in `run_sql_tool`.
        d.  The JSON string returned by `create_dataframe_tool` is the definitive data result for the SQL query. This tool also populates a shared DataFrame.
    5.  **Check for Chart Request and Generate Chart (If Applicable):**
        a.  Examine the user's original request. If it explicitly or implicitly asks for a chart (e.g., "plot", "draw", "chart", "graph", "visualize"):
            i.  You MUST call the `get_chart_generation_tool` with a clear instruction for the chart based on the user's request and the data retrieved (e.g., "Generate a bar chart of album_count by artist_name").
            ii. The `get_chart_generation_tool` will return a JSON string. This JSON string will either contain 'insights' and 'python_code' if successful, or an 'error_message' if not.
    6.  **Formulate Response (SQLSuccess):** Construct your final `SQLSuccess` response.
        a.  The `detail` field should be formatted as markdown and comprehensively contain:
            - An explanation of the SQL query and the steps taken.
            - The SQL query that was executed.
            - The complete JSON string result from `create_dataframe_tool`. This JSON string should be presented clearly within a JSON markdown code block.
            - A brief summary of the chart generation attempt (e.g., "Chart generation was successful." or "Chart generation failed: [error from tool].").
        b.  If `get_chart_generation_tool` returned a JSON string indicating successful chart generation (containing 'insights' and 'python_code'):
            - Populate the `chart_insights` field of `SQLSuccess` with the 'insights' value from the JSON.
            - Populate the `chart_python_code` field of `SQLSuccess` with the 'python_code' value from the JSON.
            - Otherwise, leave `chart_insights` and `chart_python_code` as null/None.
        b. If at any stage an error occurs (e.g., `run_sql_tool` returns an error, or `create_dataframe_tool` indicates an error) or a query yields no data (after `run_sql_tool`), explain this in the `detail` field of `SQLSuccess` or use an `InvalidRequest` response if appropriate (e.g., user request is malformed).
    
    """

@SQLAgent.tool
def list_tables_tool(ctx: RunContext[Dependencies]) -> str:
    print('list_tables_tool called')
    """Use this function to get a list of table names in the database. """
    return list_tables(ctx.deps.db_engine)

@SQLAgent.tool
def describe_table_tool(ctx: RunContext[Dependencies], table_name: str) -> str:
    print('describe_table_tool called', table_name)
    """Use this function to get a description of a table in the database."""
    return describe_table(ctx.deps.db_engine, table_name)

@SQLAgent.tool
def run_sql_tool(ctx: RunContext[Dependencies], query: str, limit: int = 10) -> str:
    print('run_sql_tool called', query)
    """Use this function to run a SQL query on the database. """
    return run_sql_query(ctx.deps.db_engine, query, limit)

@SQLAgent.tool
def create_dataframe_tool(ctx: RunContext[Dependencies], query: str) -> str:
    print('create_dataframe_tool called with query:', query)
    """\
    Use this function ONLY AFTER 'run_sql_tool' has confirmed that a query returns data.
    """
    json_output_str = create_dataframe_pd(ctx.deps.db_engine, query) # Call once

    try:
        # Attempt to parse the JSON to see if create_dataframe_pd reported an error
        data_or_error = json.loads(json_output_str)
        if isinstance(data_or_error, dict) and "error" in data_or_error:
            print(f"create_dataframe_tool: Error from create_dataframe_pd: {data_or_error['error']}")
            ctx.deps.dataframe = pd.DataFrame() # Assign empty DataFrame on error
        else:
            # If no error, convert JSON string to Pandas DataFrame
            # Use io.StringIO to avoid FutureWarning
            ctx.deps.dataframe = pd.read_json(io.StringIO(json_output_str))
            print(f"create_dataframe_tool: DataFrame populated. Shape: {ctx.deps.dataframe.shape}")
    except json.JSONDecodeError as e:
        print(f"create_dataframe_tool: JSONDecodeError parsing output from create_dataframe_pd: {e}")
        ctx.deps.dataframe = pd.DataFrame() # Assign empty DataFrame on error
    except Exception as e:
        print(f"create_dataframe_tool: Unexpected error processing data: {e}")
        ctx.deps.dataframe = pd.DataFrame() # Assign empty DataFrame on error

    return json_output_str # Return the original JSON string

@chartAgent.system_prompt
def chart_agent_system_prompt(ctx: RunContext[Dependencies]) -> str: # Renamed for clarity
    if ctx.deps.dataframe is None or ctx.deps.dataframe.empty:
        return """
        system: Error - No data available to generate a chart. The DataFrame is missing or empty.
        Please ensure data is loaded correctly before requesting a chart.
        """
    return \
    f"""
    system: You are an AI assistant specialized in creating insightful graphs and generating Python code for them.
    The data is already available in a pandas DataFrame named `df`.
    DataFrame columns: {list(ctx.deps.dataframe.columns)}
    Sample of DataFrame (first 5 rows):
    {ctx.deps.dataframe.head().to_markdown()}

    Your task:
    1.  Analyze the user's request and the provided DataFrame.
    2.  If the request is feasible, choose the most appropriate chart type from: {chartOptions}.
    3.  Generate valuable insights based on the data and the potential chart.
    4.  Produce concise and correct Python code (using matplotlib and seaborn) to plot the graph. The code should assume `df` is pre-loaded.
    5.  The Python code should be a complete, executable script that generates and shows the plot.
    6.  Return the insights and the Python code.

    If the request is unclear or cannot be fulfilled with the given data, return an `InvalidRequest` with an explanation.

    Example of Python code structure:
    ```python
    import matplotlib.pyplot as plt
    import seaborn as sns
    # df is assumed to be pre-loaded with the data

    # Your plotting code here
    # e.g., sns.barplot(data=df, x='column_x', y='column_y')
    # plt.title('Your Chart Title')
    # plt.xlabel('X-axis Label')
    # plt.ylabel('Y-axis Label')
    # plt.show() # Make sure to include this to display the plot
    ```

    When returning the results in the `ChartSuccess` object, the `python_code` field must be formatted as a Python markdown code block.
    """

@SQLAgent.tool
def get_chart_generation_tool(ctx: RunContext[Dependencies], chart_instruction: str) -> str:
    """
    Use this tool to generate a chart AFTER the data has been fetched and prepared by 'create_dataframe_tool'.
    Provide a clear instruction for the chart based on the user's request and the available data.
    The tool will use the existing DataFrame (in ctx.deps.dataframe) to generate insights and Python code.
    It returns a JSON string. If successful, this JSON string will be a dump of the ChartSuccess model (containing 'insights' and 'python_code').
    If unsuccessful, it will be a JSON string of the InvalidRequest model (containing 'error_message') or a simple error string.
    """
    print(f"\n[get_chart_generation_tool CALLED]")
    print(f"Chart Instruction: {chart_instruction}")
    print(f"DataFrame available in deps: {ctx.deps.dataframe is not None}")

    if ctx.deps.dataframe is None or ctx.deps.dataframe.empty:
        warning_msg = "Cannot generate chart: DataFrame is not available or is empty. Ensure 'create_dataframe_tool' ran successfully and returned data."
        print(warning_msg)
        return warning_msg

    print(f"DataFrame head for chart generation:\n{ctx.deps.dataframe.head()}")

    chart_agent_response_obj = chartAgent.run_sync(
        user_input=chart_instruction,
        deps=ctx.deps
    )

    print("\n--- Chart Agent Full Response Object ---")
    print(chart_agent_response_obj)
    print("--- End Chart Agent Full Response Object ---\n")

    if chart_agent_response_obj and chart_agent_response_obj.output:
        output = chart_agent_response_obj.output
        if isinstance(output, ChartResponses):
            print("--- Chart Agent Generated Output (Success) ---")
            print(f"Insights: {output.insights}")
            print(f"Python Code (markdown):\n{output.python_code}")
            print("--- End Chart Agent Generated Output ---")
             # Return a formatted string with insights and code for SQLAgent to include
            return output.model_dump_json()
        elif isinstance(output, InvalidRequest):
            error_msg = f"Chart generation failed: {output.error_message}"
            print(error_msg)
            return output.model_dump_json()
    
    failure_msg = "Chart generation failed to produce a valid response or encountered an issue."
    print(failure_msg)
    return json.dumps({"error_message": failure_msg}) 

if __name__=="__main__":
    db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')
    
    shared_deps = Dependencies(db_engine=db_engine, dataframe=None)

    user_query = "Show me how many albums each artist has, and plot this as a bar chart. List the artists and their album counts."
    print(f"User Query: {user_query}\n")

    sql_agent_final_response = SQLAgent.run_sync(user_query, deps=shared_deps)

    # print("\n--- SQL Agent Final Output (SQLResponse) ---")
    # if sql_agent_final_response and sql_agent_final_response.output:
    #     if isinstance(sql_agent_final_response.output, SQLSuccess):
    #         print(f"SQL Query Executed: {sql_agent_final_response.output.sql_query}")
    #         print(f"Details:\n{sql_agent_final_response.output.detail}")
    #         if sql_agent_final_response.output.chart_insights:
    #             print(f"\nChart Insights:\n{sql_agent_final_response.output.chart_insights}")
    #         if sql_agent_final_response.output.chart_python_code:
    #             print(f"\nChart Python Code:\n{sql_agent_final_response.output.chart_python_code}")
    #             # You can now directly access: sql_agent_final_response.output.chart_python_code
    #     elif isinstance(sql_agent_final_response.output, InvalidRequest):
    #         print(f"Error from SQL Agent: {sql_agent_final_response.output.error_message}")
    # else:
    #     print("SQL Agent did not produce a valid output.")
    print("--- End SQL Agent Final Output ---")
    # print(sql_agent_final_response.output)
    print(f"Code:\n{re.findall(r"```python\n(.*?)```", sql_agent_final_response.output.chart_python_code, re.DOTALL)}")

    # print(sql_agent_final_response.output.sql_query)
    # print(sql_agent_final_response.output.detail)
    # print(sql_agent_final_response.output.chart_python_code)