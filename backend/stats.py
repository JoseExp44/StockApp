import pandas as pd

def compute_stat(df, stat):
    """
    Compute summary statistics for the "Close" stock prices
    """
    # Data validation
    if "Close" not in df:
        return None
    close_prices = pd.to_numeric(df["Close"], errors="coerce").dropna()
    if close_prices.empty:
        return None
    
    # Calculate and return statistic
    if stat == "min":
        return float(close_prices.min())
    if stat == "max":
        return float(close_prices.max())
    if stat == "mean":
        return float(close_prices.mean())
    if stat == "median":
        return float(close_prices.median())
    if stat == "std":
        std = close_prices.std()
        return float(std) if not pd.isna(std) else None # std of one value is NaN