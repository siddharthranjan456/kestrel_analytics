from pathlib import Path
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
import yaml


ROOT = Path(__file__).resolve().parent
DB = ROOT / "output" / "kestrel.duckdb"

st.set_page_config(page_title="Kestrel Analytics", layout="wide")
st.title("Kestrel Provisions — Trusted Metrics")
st.caption("Every result comes from the documented DuckDB metric layer.")

if not DB.exists():
    st.error("Database not found. Run `python pipeline.py --generate` first.")
    st.stop()

con = duckdb.connect(str(DB), read_only=True)
catalogue = yaml.safe_load((ROOT / "config" / "metrics.yml").read_text(encoding="utf-8"))

summary, sales, operations, quality, definitions = st.tabs(
    ["Executive summary", "Sales & Finance", "Operations", "Data quality", "KPI catalogue"]
)

with summary:
    totals = con.execute("""
      SELECT SUM(gross_sales), SUM(units_sold_eaches), SUM(basket_count)
      FROM mart_sales_daily
    """).fetchone()
    excursion = con.execute("SELECT AVG(excursion_rate_pct) FROM mart_cold_chain_monthly").fetchone()[0]
    cycle = con.execute("SELECT MEDIAN(median_cycle_minutes) FROM mart_warehouse_cycle_summary").fetchone()[0]
    cols = st.columns(5)
    cols[0].metric("Gross sales", f"₹{(totals[0] or 0)/10_000_000:,.2f} Cr")
    cols[1].metric("Units sold", f"{(totals[1] or 0):,.0f}")
    cols[2].metric("Baskets", f"{(totals[2] or 0):,.0f}")
    cols[3].metric("Avg. excursion rate", f"{(excursion or 0):.2f}%")
    cols[4].metric("Median cycle", f"{(cycle or 0)/60:.1f} hours")
    trend = con.execute("SELECT business_date, SUM(gross_sales) gross_sales FROM mart_sales_daily GROUP BY 1 ORDER BY 1").df()
    st.plotly_chart(px.line(trend, x="business_date", y="gross_sales", title="Daily trusted gross sales"), use_container_width=True)

with sales:
    recon = con.execute("SELECT * FROM mart_finance_reconciliation ORDER BY week_ending, channel").df()
    st.subheader("Legacy Finance reconciliation")
    st.dataframe(recon, use_container_width=True, hide_index=True)
    with st.expander("Show SQL and definition"):
        st.write(catalogue["finance_variance"])
        st.code((ROOT / "sql/queries/finance_reconciliation.sql").read_text(), language="sql")

with operations:
    cold = con.execute("SELECT * FROM mart_cold_chain_monthly ORDER BY month, warehouse_code").df()
    cycle_df = con.execute("SELECT * FROM mart_warehouse_cycle_summary ORDER BY warehouse_code").df()
    st.plotly_chart(px.line(cold, x="month", y="excursion_rate_pct", color="warehouse_name",
                            title="Cold-chain excursion rate by warehouse"), use_container_width=True)
    st.dataframe(cycle_df, use_container_width=True, hide_index=True)
    st.info("A trip is approximated as vehicle + route + calendar day because the feed has no trip ID. Carrier analysis is not claimed because no carrier mapping is supplied.")

with quality:
    q = con.execute("SELECT * FROM data_quality ORDER BY status, feed, partition").df()
    st.dataframe(q, use_container_width=True, hide_index=True)

with definitions:
    for key, metric in catalogue.items():
        with st.expander(metric["name"]):
            st.json(metric)

con.close()

