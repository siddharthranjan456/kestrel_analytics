from pathlib import Path
import duckdb


def create_connection(database_path="output/kestrel.duckdb"):
    Path("output").mkdir(exist_ok=True)
    return duckdb.connect(database_path)