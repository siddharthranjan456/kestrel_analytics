import duckdb

con=duckdb.connect()

count = con.execute("""
    SELECT COUNT(*)
    FROM read_parquet(
        'data/raw/pos_transactions/*/*.parquet',
        union_by_name = true,
        hive_partitioning = true
    )
""").fetchone()[0]

print("POS rows:", count)