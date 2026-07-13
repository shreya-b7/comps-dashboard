import sqlite3
import pandas as pd
import os

os.makedirs("tableau/exports", exist_ok=True)

conn = sqlite3.connect("db/comps.db")

# --- Main comps table: one row per ticker per quarter, with key metrics joined ---
comps_table = pd.read_sql_query("""
    SELECT c.ticker, c.sub_vertical, f.quarter, f.revenue, f.revenue_growth_qoq,
           f.gross_margin, f.fcf_margin, e.ev_revenue_multiple, r.rule_of_40_score
    FROM companies c
    JOIN financials f ON c.ticker = f.ticker
    LEFT JOIN ev_revenue e ON c.ticker = e.ticker AND f.quarter = e.quarter
    LEFT JOIN rule_of_40 r ON c.ticker = r.ticker AND f.quarter = r.quarter
""", conn)
comps_table.to_csv("tableau/exports/comps_table.csv", index=False)

# --- Average EV/Revenue by sub-vertical (for the peer comparison bar chart) ---
ev_by_vertical = pd.read_sql_query("""
    SELECT c.sub_vertical, AVG(e.ev_revenue_multiple) AS avg_ev_revenue
    FROM companies c
    JOIN ev_revenue e ON c.ticker = e.ticker
    WHERE e.ev_revenue_multiple IS NOT NULL
    GROUP BY c.sub_vertical
""", conn)
ev_by_vertical.to_csv("tableau/exports/ev_revenue_by_vertical.csv", index=False)

# --- Full Rule of 40 scores with peer rank (for reference/drill-down) ---
rule_of_40_scores = pd.read_sql_query("""
    SELECT c.ticker, c.sub_vertical, r.quarter, r.rule_of_40_score,
           RANK() OVER (PARTITION BY c.sub_vertical ORDER BY r.rule_of_40_score DESC) AS rank_in_vertical
    FROM rule_of_40 r
    JOIN companies c ON c.ticker = r.ticker
    WHERE r.rule_of_40_score IS NOT NULL
""", conn)
rule_of_40_scores.to_csv("tableau/exports/rule_of_40_scores.csv", index=False)

conn.close()

print("Exported 3 CSVs to tableau/exports/")
print(f"comps_table: {len(comps_table)} rows")
print(f"ev_revenue_by_vertical: {len(ev_by_vertical)} rows")
print(f"rule_of_40_scores: {len(rule_of_40_scores)} rows")