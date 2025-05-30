import polars as pl
from sqlalchemy import Engine, create_engine
import json

def create_dataframe(engine: Engine, query: str):
    try:
        with engine.connect() as conn:
            df = pl.read_database(query=query, connection=conn)
            return json.dumps(df.write_json())
    except Exception as e:
        return json.dumps({"error": f"Error processing query results: {str(e)}", "data": []})

# db_engine = create_engine('postgresql+psycopg2://chinook:chinook@localhost:5433/chinook_auto_increment')

# print(create_dataframe(db_engine, "SELECT ar.name AS artist_name, COUNT(DISTINCT al.album_id) AS album_count FROM artist ar JOIN album al ON ar.artist_id = al.artist_id JOIN track t ON al.album_id = t.album_id JOIN genre g ON t.genre_id = g.genre_id WHERE g.name = 'Metal' GROUP BY ar.name;;"))
