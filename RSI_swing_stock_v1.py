import json
import time
import threading
from dhanhq import marketfeed
from Dhan_Tradehull import Tradehull
import talib
import pandas as pd
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")
version = "v2"

# File path for stock data
file_path = "stock_data.json"

# Global dictionary to store RSI values
rsi_cache = {}

# Load stock data from JSON file
def load_stock_data(file_path):
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return {}

# Save stock data to JSON file
def save_stock_data(file_path, data):
    try:
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error saving JSON file: {e}")

# Generate instruments list for subscription
def get_instruments(stock_data):
    instruments = []
    for stock in stock_data.values():
        exchange_segment = marketfeed.NSE
        security_id = stock["security_token"]
        instruments.append((exchange_segment, str(security_id), marketfeed.Quote))
    return instruments

# Background thread function to fetch RSI data
def update_rsi_values():
    global rsi_cache
    tsl = Tradehull(ClientCode=client_id, token_id=access_token)

    while True:
        print("Fetching RSI data...")
        for stock in stock_data.keys():
            try:
                chart_daily = tsl.get_historical_data(stock, "NSE", "DAY")
                print(chart_daily)
                # chart_intraday = tsl.get_intraday_data(stock,"NSE",5)
                # print(chart_intraday)
                rsi = talib.RSI(pd.Series(chart_daily["close"]), 7)
                rsi_cache[stock] = round(rsi.iloc[-1], 2)  # Cache latest RSI value
            except Exception as e:
                print(f"Error fetching RSI for {stock}: {e}")
        
        print("RSI data updated.")
        time.sleep(300)  # Fetch RSI every 5 minutes

# Start the RSI fetching thread
rsi_thread = threading.Thread(target=update_rsi_values, daemon=True)
rsi_thread.start()

# Load stock data
stock_data = load_stock_data(file_path)

# Dhan API connection
instruments = get_instruments(stock_data)
data = marketfeed.DhanFeed(client_id, access_token, instruments, version)

def update_stock_data(response):
    security_id = str(response.get("security_id"))
    
    for stock, details in stock_data.items():
        if str(details["security_token"]) == security_id:
            details["high"] = float(response.get("high", details["high"]))
            details["low"] = float(response.get("low", details["low"]))
            details["current"] = float(response.get("LTP", details["current"]))
            details["close"] = float(response.get("close", details["close"]))
            details["total_buy_quantity"] = float(response.get("total_buy_quantity", details["total_buy_quantity"]))
            details["total_sell_quantity"] = float(response.get("total_sell_quantity", details["total_sell_quantity"]))

            # Assign RSI from cache (avoid blocking WebSocket updates)
            details["rsi"] = rsi_cache.get(stock, "N/A")  # Use cached RSI

            if details["low"] > 0:
                details["percent_change_from_low_to_current"] = round(
                    ((details["current"] - details["low"]) / details["low"]) * 100, 2
                )

            # print(f"Updated {stock}: Price={details['current']}, RSI={details['rsi']}")
            break

try:
    last_save_time = time.time()
    
    while True:
        start_time = time.time()
        data.run_forever()
        response = data.get_data()
        
        if response:
            update_stock_data(response)

        # Save updates every 30 seconds
        if time.time() - last_save_time >= 30:
            save_stock_data(file_path, stock_data)
            last_save_time = time.time()
            print("Stock data updated and saved.")

except Exception as e:
    print(e)
finally:
    data.disconnect()
