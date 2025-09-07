"""
Frontend data event handlers: backend processes request and frontend displays.
Uses PyLinkJS jsc.eval_js_code() to act as bridge between frontend/backend.

- ready: initialize UI and send default dates/tickers to the page.
--JS callback: frontend sets given UI and default values.
- get_plot_data: filter one ticker by date and send x/y arrays.
--JS callback: frontend plots x/y arrays.
- get_stat_value: compute mean/median/std and send overlay values.
--JS callback: frontend plots overlay lines.
"""


import os
import pandas as pd
from datetime import date, timedelta
from .config import TICKERS, DATA_DIR
from .data import load_data, filter_by_date


def ready(jsc, origin, pathname, search, *args):
    """
    Initialize the frontend by sending available tickers and default dates.
    The default window is the latest 30 days.
    
    Args:
    jsc: PyLinkJS client for this tab.
    origin: Page origin string.
    pathname: Page path.
    search: Query string.
    *args: Extra values.

    Returns:
        None

    JS callback:
        window.initApp(tickerList: string[], defaultStart: 'YYYY-MM-DD', defaultEnd: 'YYYY-MM-DD')
    """
    tickers = [t for t in TICKERS if os.path.exists(os.path.join(DATA_DIR, f"{t}.csv"))]

    default_end = date.today()
    default_start = default_end - timedelta(days=30)
    
    # Explicitly set dates to iso format for front end
    default_start = default_start.isoformat()
    default_end = default_end.isoformat()

    # Dates to strings for the date inputs
    jsc.eval_js_code(
        f"window.initApp({tickers}, '{default_start}', '{default_end}');"
    )


def get_plot_data(jsc, ticker, start, end):
    """
    Provide X (date strings) and Y (Close prices) for the chart, or an error message.

    Args:
        jsc: PyLinkJS client.
        ticker: Ticker symbol (e.g., 'AAPL').
        start: Start date 'YYYY-MM-DD'.
        end: End date 'YYYY-MM-DD'.
    
    Returns:
        None

    JS callback:
        window.plotStockData(x: string[], y: number[], errorMsg: string|null)
    """
    df = load_data(ticker)
    if df.empty:
        jsc.eval_js_code("window.plotStockData([], [], 'No data available');")
        return

    filtered = filter_by_date(df, start, end)
    if filtered.empty:
        jsc.eval_js_code("window.plotStockData([], [], 'No data for selected range');")
        return

    # return lists to JS to be read as arrays
    x = [pd.to_datetime(d).strftime("%m/%d/%Y") for d in filtered["Date"]]
    y = [float(c) for c in filtered["Close"]]
    jsc.eval_js_code(f"window.plotStockData({x}, {y}, null);")


def get_stat_value(jsc, ticker, start, end, stat):
    """
    Compute a requested statistic and return overlay line(s) for the chart.

    Args:
    jsc: PyLinkJS client.
    ticker: Ticker symbol (e.g., 'AAPL').
    start: Start date 'YYYY-MM-DD'.
    end: End date 'YYYY-MM-DD'.
    stat: 'mean', 'median', or 'std'.

    Returns:
        None

    JS callback:
        window.drawStatLine(
            stat: 'mean'|'median'|'std',
            upper: number|null,
            lower: number|null,
            errorMsg: string|null
        )
    """
    df = load_data(ticker)

    filtered = filter_by_date(df, start, end)
    
    # convert to price series to utilize mean, median, std dev pandas functions
    price = pd.to_numeric(filtered.get("Close", pd.Series(dtype=float)), errors="coerce").dropna()

    s = stat.lower()

    if s == "mean":
        val = float(price.mean())
        jsc.eval_js_code(f"window.drawStatLine('mean', {val}, null, null);")
        return

    if s == "median":
        val = float(price.median())
        jsc.eval_js_code(f"window.drawStatLine('median', {val}, null, null);")
        return

    if s == "std":
        n = len(price)
        if n == 1:
            jsc.eval_js_code("window.drawStatLine('std', null, null, 'Only one price point, two required for std dev.');")
            return
        mean = price.mean()
        std = price.std()  
        upper = float(mean + std)
        lower = float(mean - std)
        jsc.eval_js_code(f"window.drawStatLine('std', {upper}, {lower}, null);")
        return

