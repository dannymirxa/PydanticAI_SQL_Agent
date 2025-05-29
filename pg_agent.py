from dataclasses import dataclass
from typing import Annotated
import asyncpg
from annotated_types import MinLen
from pydantic import BaseModel, Field

@dataclass
class Deps:
    conn: asyncpg.Connection

class Success(BaseModel):
    sql_query: Annotated[str, MinLen(1)]
    explanation: str = Field("", description="Explanation of the SQL query, as markdown")

class InvalidRequest(BaseModel):
    error_message: str