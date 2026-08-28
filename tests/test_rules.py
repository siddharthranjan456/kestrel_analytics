from pathlib import Path
import duckdb
import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_temperature_conversion():
    result = duckdb.sql("SELECT (50.0-32.0)*5.0/9.0").fetchone()[0]
    assert round(result, 2) == 10.0


def test_deduplication_rule():
    result = duckdb.sql("""
      WITH x(txn_id,line_no,ingest_date) AS (
        VALUES ('T1',1,DATE '2026-01-01'), ('T1',1,DATE '2026-01-02'), ('T2',1,DATE '2026-01-01')
      )
      SELECT COUNT(*) FROM (
        SELECT * FROM x QUALIFY ROW_NUMBER() OVER (
          PARTITION BY txn_id,line_no ORDER BY ingest_date DESC
        )=1
      )
    """).fetchone()[0]
    assert result == 2


def test_cdc_latest_wins_and_delete_is_removed():
    result = duckdb.sql("""
      WITH x(id,op,ts,seq) AS (
        VALUES ('A','I',TIMESTAMP '2026-01-01',1), ('A','D',TIMESTAMP '2026-01-02',2),
               ('B','I',TIMESTAMP '2026-01-01',3), ('B','U',TIMESTAMP '2026-01-02',4)
      )
      SELECT COUNT(*) FROM (
        SELECT * FROM x QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts DESC,seq DESC)=1
      ) WHERE op <> 'D'
    """).fetchone()[0]
    assert result == 1


def test_kpi_catalogue_has_required_fields():
    catalogue = yaml.safe_load((ROOT / "config/metrics.yml").read_text())
    required = {"name", "definition", "grain", "formula", "filters", "exclusions", "sources", "owner", "limitations", "query"}
    assert len(catalogue) >= 5
    assert all(required <= set(metric) for metric in catalogue.values())

