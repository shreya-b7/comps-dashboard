import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect("db/comps.db")

    # --- Load companies table ---
    tickers_df = pd.read_csv("data/raw/tickers.csv")
    # tickers.csv only has ticker + sub_vertical — fill in placeholders for name/sector for now
    companies_df = tickers_df.copy()
    companies_df["name"] = None
    companies_df["sector"] = None
    companies_df = companies_df[["ticker", "name", "sector", "sub_vertical"]]

    companies_df.to_sql("companies", conn, if_exists="replace", index=False)

    # --- Load financials table ---
    financials_df = pd.read_csv("data/processed/financials.csv")
    # keep only the columns the financials table actually has
    financials_to_load = financials_df[
        ["ticker", "quarter", "revenue", "revenue_growth_qoq", "gross_margin", "fcf_margin"]
    ]
    financials_to_load.to_sql("financials", conn, if_exists="replace", index=False)

    # --- Load market_data table ---
    # market_cap and ev live inside financials.csv from our pull script, one row per quarter —
    # pull them out into their own table, using 'quarter' as the date
    market_data_df = financials_df[["ticker", "quarter", "market_cap", "ev"]].copy()
    market_data_df = market_data_df.rename(columns={"quarter": "date"})
    market_data_df.to_sql("market_data", conn, if_exists="replace", index=False)

    # --- Run the SQL views (Step 8) right away so they're ready to query ---
    with open("scripts/views.sql") as f:
        conn.executescript(f.read())

    conn.commit()

    # Quick sanity check
    for table in ["companies", "financials", "market_data"]:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {count} rows")

    conn.close()

if __name__ == "__main__":
    main()