import sqlite3

def main():
    conn = sqlite3.connect("db/comps.db")
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS companies (
        ticker TEXT PRIMARY KEY,
        name TEXT,
        sector TEXT,
        sub_vertical TEXT
    );

    CREATE TABLE IF NOT EXISTS financials (
        ticker TEXT,
        quarter TEXT,
        revenue REAL,
        revenue_growth_qoq REAL,
        gross_margin REAL,
        fcf_margin REAL,
        FOREIGN KEY(ticker) REFERENCES companies(ticker)
    );

    CREATE TABLE IF NOT EXISTS market_data (
        ticker TEXT,
        date TEXT,
        market_cap REAL,
        ev REAL,
        FOREIGN KEY(ticker) REFERENCES companies(ticker)
    );
    """)

    conn.commit()
    conn.close()
    print("Schema created successfully in db/comps.db")

if __name__ == "__main__":
    main()