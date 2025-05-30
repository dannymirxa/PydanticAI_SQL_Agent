from textwrap import dedent
from dataclasses import dataclass
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from sqlalchemy import Engine, create_engine
from load_models import OPENAI_MODEL
from sql import list_tables, describe_table, run_sql_query
from dataframe import create_dataframe_pd
from typing import Annotated
from annotated_types import MinLen
from typing_extensions import TypeAlias, Union
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import re


@dataclass
class Dependencies:
    # db_engine: Engine
    dataframe: pd.DataFrame

class Success(BaseModel):
    explanation: Annotated[str, MinLen(1), Field(
        alias='explanation',
        description="Explanation of the Python code"
    )]
    insights: Annotated[str, MinLen(1), Field(
        alias='insights',
        description="insights from the dataset and graph"
    )]
    python_code: Annotated[str, MinLen(1), Field(
        alias='python_code',
        description='Python code to plot the graph, as markdown'
    )]

class InvalidRequest(BaseModel):
    error_message: str

Response: TypeAlias = Union[Success, InvalidRequest]

chart_agent = Agent(
        name='Chart Agent',
        model=OPENAI_MODEL,
        # system_prompt=[system_prompt],
        output_type=Response
)

option = ('Scatter', 'Line', 'Histograph', 'Bargraph', 'Pie Chart')

@chart_agent.system_prompt
async def system_prompt(ctx: RunContext[Dependencies]) -> str:
    return \
    f"""
        system: you are an AI assistant that will make best fit graph and valuabe insights from the dataset content and also write short and complete python code to plot graphs. 
                dataset columns names are - {ctx.deps.dataframe.columns}. data is already read in df.

        human: this is the sample of the dataset values (df.head(10) - {ctx.deps.dataframe.head(10)})

        note - read the user input and look for the graph type among these: {option}
        note - based on the user input, pick only one of the graph type
        note - produce valuable insights from the dataset and the graph
        note - only use matplotlib and seaborn

        When returning the results in the `Success` object, the `python_code` field should be formatted as markdown.
    """

def create_dataframe_pl(engine: Engine, query: str):
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query=query, con=conn)
            return json.dumps(df.write_json())
    except Exception as e:
        return json.dumps({"error": f"Error processing query results: {str(e)}", "data": []})

if __name__ == '__main__':
    
    db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')
    df = create_dataframe_pd(db_engine, "SELECT ar.name AS artist_name, COUNT(DISTINCT al.album_id) AS album_count FROM artist ar JOIN album al ON ar.artist_id = al.artist_id JOIN track t ON al.album_id = t.album_id JOIN genre g ON t.genre_id = g.genre_id WHERE g.name = 'Metal' GROUP BY ar.name;")

    deps = Dependencies(dataframe=df)

    response1 = chart_agent.run_sync("Using bar chart, show how many album for each artist", deps=deps)
    
    print(response1.output.explanation)
    print(response1.output.insights)
    print(response1.output.python_code)

    # print(dedent(response1.output.python_code))

    # code_blocks = re.findall(r"```(.*?)```", response1.output.python_code)

    exec_globals = {"df": df, "sns": sns, "plt": plt, "pd": pd}

    code_blocks = str(response1.output.python_code).replace("```", "")
    code_blocks = code_blocks.replace("python", "")
    print(code_blocks)
    exec(code_blocks, exec_globals)

