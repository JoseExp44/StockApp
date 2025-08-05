"""
handlers.py

Defines pylink.js event handler functions for frontend-backend communication.
Handles initial UI setup and data retrieval for plotting and statistics.
"""

import os
import pandas as pd
import numpy as np
from .config import TICKERS, DATA_DIR
from .data import load_data, filter_by_date

def ready(jsc, origin, pathname, search, *args):
    """
    Called by pylink.js when the web app loads.
    Initializes the frontend UI: provides available tickers and global date range,
    and sets default date window to latest 30 days.
    """
    tickers = [t for t in TICKERS if os.path.exists(os.path.join(DATA_DIR, f"{t}.csv"))]
    all_dates = []
    for t in tickers:
        df = load_data(t)
        if not df.empty:
            all_dates += list(df["Date"])
    min_date, max_date, default_start, default_end = None, None, None, None
    if all_dates:
        all_dates = pd.to_datetime(all_dates, errors='coerce').dropna()
        min_date = all_dates.min().date()
        max_date = all_dates.max().date()
        default_end = max_date
        default_start = max(min_date, (default_end - pd.Timedelta(days=30)))
    jsc.eval_js_code(
        f"window.initApp({tickers}, '{min_date}', '{max_date}', '{default_start}', '{default_end}');"
    )

def get_plot_data(jsc, ticker, start, end):
    """
    Called by frontend to retrieve date/price data for plotting.
    Returns X (dates) and Y (Close prices) lists.
    """
    df = load_data(ticker)
    if df.empty:
        jsc.eval_js_code("window.plotStockData([], [], 'No data available');")
        return

    filtered = filter_by_date(df, start, end)
    if filtered.empty or "Close" not in filtered:
        jsc.eval_js_code("window.plotStockData([], [], 'No data for selected range');")
        return

    # Build lists for X and Y
    x = [pd.to_datetime(d).strftime("%m/%d/%Y") for d in filtered["Date"]]
    y = [float(c) if pd.notna(c) else None for c in filtered["Close"]]
    # Send to frontend (errorMsg is null)
    jsc.eval_js_code(f"window.plotStockData({x}, {y}, null);")

def get_stat_value(jsc, ticker, start, end, stat):
    """
    Called by frontend to get the value(s) needed to plot stat lines.
    """
    df = load_data(ticker)
    if df.empty:
        jsc.eval_js_code("window.drawStatLine(null, null, null, null);")
        return

    filtered = filter_by_date(df, start, end)
    price = pd.to_numeric(filtered["Close"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if price.empty:
        jsc.eval_js_code("window.drawStatLine(null, null, null, null);")
        return
    
    stat = stat.lower()
    if stat == "mean":
        mean = price.mean()
        mean = float(mean) if not pd.isna(mean) else None
        jsc.eval_js_code(f"window.drawStatLine('mean', {mean}, null, null);")
    elif stat == "median":
        median = price.median()
        median = float(median) if not pd.isna(median) else None
        jsc.eval_js_code(f"window.drawStatLine('median', {median}, null, null);")
    elif stat == "std":
    mean = price.mean()
    std = price.std()
    if not pd.isna(mean) and not pd.isna(std):
        upper = mean + std
        lower = mean - std
    else:
        upper = lower = None
    jsc.eval_js_code(
        f"window.drawStatLine('std', "
        f"{mean if mean is not None else 'null'}, "
        f"{upper if upper is not None else 'null'}, "
        f"{lower if lower is not None else 'null'});"
    )