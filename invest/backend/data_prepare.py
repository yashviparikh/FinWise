import csv
import time
from . import db, app
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from .models import StockData

def fetch_and_store(symbol):
    """
    Fetch all daily data from 2023-01-01 to yesterday and safely insert into DB.
    Skips rows already in DB.
    """
    if not symbol or symbol.upper() == "SYMBOL.NS":
        print(f"Skipping placeholder symbol {symbol}")
        return 0

    start_date = "2023-01-01"
    end_date = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        data = yf.download(symbol, start=start_date, end=end_date, interval="1d", auto_adjust=True)
        if data.empty:
            print(f"No data for {symbol}. Skipping...")
            return 0

        # Flatten MultiIndex if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]

        data = data.reset_index()
        inserted = 0

        for i, row in data.iterrows():
            try:
                date_value = pd.to_datetime(row["Date"]).date()

                # Skip if this row already exists
                exists = StockData.query.filter_by(symbol=symbol[:30], date=date_value).first()
                if exists:
                    continue

                stock = StockData(
                    symbol=symbol[:30],
                    date=date_value,
                    open=float(row["Open"]) if not pd.isna(row["Open"]) else None,
                    high=float(row["High"]) if not pd.isna(row["High"]) else None,
                    low=float(row["Low"]) if not pd.isna(row["Low"]) else None,
                    close=float(row["Close"]) if not pd.isna(row["Close"]) else None,
                    adj_close=float(row["Adj Close"]) if "Adj Close" in row and not pd.isna(row["Adj Close"]) else float(row["Close"]),
                    volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else 0
                )

                db.session.add(stock)
                db.session.commit()  # Commit each row immediately
                inserted += 1

            except Exception as e:
                print(f"Error adding row for {symbol} on {date_value}: {e}")
                db.session.rollback()

        print(f"Inserted {inserted} rows for {symbol}")
        return inserted

    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        db.session.rollback()
        return 0

def update_stocks(csv_file="invest/stock_list.csv", start_index=1971, delay=1):
    """
    Fetch and store data for symbols starting from start_index in CSV.
    Safe, resumable for large batches.
    """
    failed_symbols = []

    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        symbols = [row[0].strip() + ".NS" for row in reader if row and row[0].strip()]

    symbols_to_process = symbols[start_index:]
    print(f"Total symbols to process: {len(symbols_to_process)}")

    for idx, symbol in enumerate(symbols_to_process, start=start_index+1):
        print(f"\nProcessing symbol {idx}/{len(symbols)}: {symbol}")
        try:
            fetch_and_store(symbol)
        except Exception as e:
            print(f"Failed processing {symbol}: {e}")
            db.session.rollback()
            failed_symbols.append(symbol)
        time.sleep(delay)

    print(f"\nFinished processing {len(symbols_to_process)} symbols.")
    if failed_symbols:
        print("Failed or empty symbols:", failed_symbols)

if __name__ == '__main__':
    with app.app_context():
        # Insert remaining 1115 stocks starting from 1001st symbol
        update_stocks(csv_file="invest/stock_list.csv", start_index=1971, delay=1)
