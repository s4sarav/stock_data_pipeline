import pandas as pd
import os
import yfinance as yf
import duckdb
from datetime import datetime

# 1. Fetch live data for specific US Stock Tickers using yfinance
def fetch_stock_data():
    tickers = ["AAPL", "TSLA", "MSFT", "NVDA"]
    print(f"Fetching live market data for tickers: {', '.join(tickers)}...")
    
    # Download the most recent 1 day of data at 1-minute intervals
    data = yf.download(tickers, period="1d", interval="1m", group_by="ticker")
    return data, tickers

# 2. Process the data and load it into DuckDB
def load_to_duckdb(data, tickers):
    print("Connecting to local DuckDB database...")
    conn = duckdb.connect("stock_warehouse.db")
    
    ingested_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    processed_records = []
    
    for ticker in tickers:
        ticker_data = data[ticker].dropna()
        for timestamp, row in ticker_data.iterrows():
            processed_records.append({
                "ticker": ticker,
                "timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "open_price": float(row["Open"]),
                "high_price": float(row["High"]),
                "low_price": float(row["Low"]),
                "close_price": float(row["Close"]),
                "volume": int(row["Volume"]),
                "ingested_at": ingested_at
            })
            
    print(f"Parsed {len(processed_records)} individual stock price entries.")

    # 🌟 THE FIX: Convert the list of dictionaries into a structured Pandas DataFrame
    df_records = pd.DataFrame(processed_records)

    # Create the landing table inside DuckDB if it doesn't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS raw_stocks (
            ticker VARCHAR,
            timestamp TIMESTAMP,
            open_price DOUBLE,
            high_price DOUBLE,
            low_price DOUBLE,
            close_price DOUBLE,
            volume BIGINT,
            ingested_at TIMESTAMP
        )
    """)
    
    # 🌟 THE FIX: Select directly from your new Pandas DataFrame variable
    conn.execute("INSERT INTO raw_stocks SELECT * FROM df_records")
    
    # Verify the results and print metrics
    row_count = conn.execute("SELECT COUNT(*) FROM raw_stocks").fetchone()[0]
    print(f"🎉 Success! Total records in DB: {row_count}")
        
    conn.close()
    

if __name__ == "__main__":
    try:
        raw_data, tickers = fetch_stock_data()
        load_to_duckdb(raw_data, tickers)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
