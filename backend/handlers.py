import os
import pandas as pd
from .config import TICKERS, DATA_DIR
from .data import load_data, filter_by_date
from .stats import compute_stat

def ready(jsc, origin, pathname, search, *args):
    """
    Called by pylink.js when the frontend first loads.
    Initializes frontend UI components: provides date range
    """
    # Loads date range
    tickers = [t for t in TICKERS if os.path.exists(os.path.join(DATA_DIR, f"{t}.csv"))]
    all_dates = []
    for t in tickers:
        df = load_data(t)
        if not df.empty:
            all_dates += list(df["Date"])
    min_date, max_date = None, None 
    if all_dates:   
        all_dates = pd.to_datetime(all_dates, errors="coerce")
        min_date = str(all_dates.min().date())
        max_date = str(all_dates.max().date())
    
    # Send date range to the frontend
    jsc.eval_js_code(f"window.initApp('{min_date}', '{max_date}')")
    

def get_stats(jsc, stat, start, end):
    """
    Called by frontend when statistic button is pressed
    Provides ticker statistic values for frontend statistic table 
    """
    stat_results = {}
    for ticker in TICKERS:
        ticker_df = load_data(ticker)
        if ticker_df.empty:
            stat_results[ticker] = None 
        else:
            date_filtered_df = filter_by_date(ticker_df, start, end)
            stat_results[ticker] = compute_stat(date_filtered_df, stat)
    
    # send stat values to the frontend
    jsc.eval_js_code(f"window.showStatResults('{stat}', {stat_results});")