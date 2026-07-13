import os
import time
import json
import pandas as pd
import yfinance as yf

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"


def pull_ticker(ticker):
    """Pull quarterly income statement, balance sheet, cash flow, and info for one ticker."""
    t = yf.Ticker(ticker)

    income = t.quarterly_income_stmt      # rows = line items, columns = quarter-end dates
    balance = t.quarterly_balance_sheet
    cashflow = t.quarterly_cashflow
    info = t.info                          # dict with marketCap, sector, etc.

    # Timestamp column headers break json.dump (Timestamps can't be dict KEYS, only values),
    # so convert columns to plain strings on a copy before saving the raw snapshot.
    def stringify_columns(df):
        if df is None or df.empty:
            return {}
        df_copy = df.copy()
        df_copy.columns = df_copy.columns.astype(str)
        return df_copy.to_dict()

    raw_snapshot = {
        "income": stringify_columns(income),
        "balance": stringify_columns(balance),
        "cashflow": stringify_columns(cashflow),
        "info": {k: v for k, v in info.items() if isinstance(v, (str, int, float, type(None)))},
    }
    with open(f"{RAW_DIR}/{ticker}.json", "w") as f:
        json.dump(raw_snapshot, f, indent=2, default=str)

    return income, balance, cashflow, info


def flatten_ticker_data(ticker, income, balance, cashflow, info):
    """Turn one ticker's yfinance data into a list of row dicts, one per quarter."""
    rows = []

    if income is None or income.empty:
        return rows

    market_cap = info.get("marketCap")  # current snapshot only, not historical per quarter

    for date in income.columns:
        revenue = income.loc["Total Revenue", date] if "Total Revenue" in income.index else None
        gross_profit = income.loc["Gross Profit", date] if "Gross Profit" in income.index else None

        gross_margin = (gross_profit / revenue) if (revenue and gross_profit is not None) else None

        # FCF: yfinance provides a pre-computed "Free Cash Flow" row directly
        fcf = None
        if cashflow is not None and date in cashflow.columns:
            if "Free Cash Flow" in cashflow.index:
                fcf = cashflow.loc["Free Cash Flow", date]
        fcf_margin = (fcf / revenue) if (fcf is not None and revenue) else None

        # EV = market cap + total debt - cash (computed manually, current snapshot)
        total_debt = None
        cash = None
        if balance is not None and date in balance.columns:
            if "Total Debt" in balance.index:
                total_debt = balance.loc["Total Debt", date]
            if "Cash And Cash Equivalents" in balance.index:
                cash = balance.loc["Cash And Cash Equivalents", date]
        ev = None
        if market_cap is not None and total_debt is not None and cash is not None:
            ev = market_cap + total_debt - cash

        rows.append({
            "ticker": ticker,
            "quarter": date,
            "revenue": revenue,
            "gross_margin": gross_margin,
            "fcf_margin": fcf_margin,
            "market_cap": market_cap,
            "ev": ev,
        })

    return rows


def add_growth_metrics(df):
    """Compute quarter-over-quarter revenue growth.
    Note: yfinance's free quarterly statements typically only return ~4 recent quarters,
    which isn't enough history for a true year-over-year (4-quarter-back) comparison.
    QoQ growth is the honest substitute given that data constraint."""
    df["quarter"] = pd.to_datetime(df["quarter"])
    df = df.sort_values(["ticker", "quarter"])
    df["revenue_growth_qoq"] = df.groupby("ticker")["revenue"].pct_change(periods=1)
    return df


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    tickers_df = pd.read_csv(f"{RAW_DIR}/tickers.csv")
    tickers = tickers_df["ticker"].tolist()

    # --- Test with ONE ticker first ---
    print("Running a single-ticker test (AAPL) before pulling your full list...")
    income, balance, cashflow, info = pull_ticker("AAPL")
    if income is None or income.empty:
        print("\n[STOPPED] The test pull for AAPL returned no income statement data.")
        print("yfinance may be temporarily rate-limiting or Yahoo may have changed something.")
        print("Wait a minute and try again, or check github.com/ranaroussi/yfinance/issues")
        print("for any current outage reports.")
        return
    print("Test pull succeeded — proceeding with full ticker list.\n")

    all_rows = []
    failed_tickers = []

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] Pulling {ticker}...")
        try:
            income, balance, cashflow, info = pull_ticker(ticker)
            rows = flatten_ticker_data(ticker, income, balance, cashflow, info)
            if not rows:
                print(f"  [!] No data returned for {ticker}, skipping.")
                failed_tickers.append(ticker)
            all_rows.extend(rows)
        except Exception as e:
            print(f"  [!] {ticker} failed: {e}")
            failed_tickers.append(ticker)
        time.sleep(1.5)  # yfinance rate-limits more aggressively than a real API — be conservative

    if not all_rows:
        print("\n[WARNING] No data was collected across any ticker. Nothing to save.")
        return

    financials_df = pd.DataFrame(all_rows)
    financials_df = financials_df.dropna(subset=["revenue"])  # drop incomplete/unusable quarters
    financials_df = add_growth_metrics(financials_df)

    output_path = f"{PROCESSED_DIR}/financials.csv"
    financials_df.to_csv(output_path, index=False)
    print(f"\nDone. Saved {len(financials_df)} rows to {output_path}")

    if failed_tickers:
        print(f"\n{len(failed_tickers)} tickers failed and were skipped: {failed_tickers}")
        print("You can re-run just these later, or drop them from tickers.csv.")


if __name__ == "__main__":
    main()
