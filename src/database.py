from pathlib import Path
import duckdb


def connect(database_path: Path, read_only: bool = False):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(database_path), read_only=read_only)


def sql_list(paths: list[Path]) -> str:
    """Return a safely quoted DuckDB SQL list of file paths."""
    if not paths:
        raise ValueError("At least one readable file is required")
    quoted = ["'" + str(p.resolve()).replace("'", "''").replace("\\", "/") + "'" for p in paths]
    return "[" + ",".join(quoted) + "]"

