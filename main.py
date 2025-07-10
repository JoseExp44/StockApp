import argparse
import sys
from backend.config import SERVER_PORT
from backend.data import download_data
from backend import handlers
from pylinkjs import PyLinkJS

def main():
    print("Downloading stock data for all tickers...")
    download_data()
    print("Download complete.")

    # Register handlers
    PyLinkJS.ready = handlers.ready        
    PyLinkJS.get_stats = handlers.get_stats

    print(f"Starting web server on port {SERVER_PORT}...")
    PyLinkJS.run_pylinkjs_app(
        default_html='frontend/stock_app.html',  
        port=SERVER_PORT                          
    )

if __name__ == "__main__":
    main()
