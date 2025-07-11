import os

# Ticker Data 
TICKERS = ['AAPL', 'MSFT', 'IBM'] 
DOWNLOAD_PERIOD = "1y" # "1d", "1mo", "1y" before current date
DOWNLOAD_INTERVAL = "1d" # 1d interval between data points
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Server 
SERVER_PORT = int(os.environ.get("PORT", 8300))

# Ensure data directory exists during import before any data access
os.makedirs(DATA_DIR, exist_ok=True)