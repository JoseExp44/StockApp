import os
import pandas as pd
import yfinance as yf
from .config import TICKERS, DATA_DIR, DOWNLOAD_PERIOD, DOWNLOAD_INTERVAL

def download_data():
    """
    Downloads historical data for each Ticker in TICKERS
    - Skips tickers that don't exist
    - Saves each as CSV in DATA_DIR to prevent api source bottlenecks
    """
    for ticker in TICKERS:
        try: 
            df = yf.download(
                ticker,
                period=DOWNLOAD_PERIOD,
                interval=DOWNLOAD_INTERVAL,
                auto_adjust=True,   ##accounts for stock calculations
                progress=False      ##progress bar in console while downloading
            )
            if df.empty:
                print(f"Warning: no data for {ticker}, skipping.")
                continue
            df.reset_index(inplace=True)
            csv_path = os.path.join(DATA_DIR, f"{ticker}.csv")
            df.to_csv(csv_path, index=False)
        except Exception as e:
            print(f"Error downloading {ticker}: {e}")

def load_data(ticker):
    """
    Load CSV data for a single ticker as a DataFrame.
    """
    csv_path = os.path.join(DATA_DIR, f"{ticker}.csv")
    if not os.path.exists(csv_path):
        return pd.DataFrame()
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    return df

def filter_by_date(df, start, end):
    """
    Filters only rows with Date between start and end (inclusive).
    """
    if "Date" not in df or df.empty:
        return pd.DataFrame()
    df = df.copy() 
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce") 
    mask = (df["Date"] >= pd.to_datetime(start)) & (df["Date"] <= pd.to_datetime(end))
    return df.loc[mask]
    