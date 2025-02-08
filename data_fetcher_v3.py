

import json
import time
from dhanhq import marketfeed
from Dhan_Tradehull import Tradehull
import talib


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

# File path for stock data
file_path = "stock_data.json"
stock_data = load_stock_data(file_path)

# Dhan API credentials
from dotenv import load_dotenv
import os
# loaded environment variable
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")
version = "v2"

# Subscribe to instruments
instruments = get_instruments(stock_data)

data = marketfeed.DhanFeed(client_id, access_token, instruments, version)
tsl = Tradehull(ClientCode=client_id, token_id=access_token)

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
            chart = tsl.get_historical_data(stock,"NSE", "DAY")
            rsi = talib.RSI(chart["close"],7)
            details["rsi"] = rsi[10]
            print(rsi[10])
            if details["low"] > 0:
                details["percent_change_from_low_to_current"] = round(
                    ((details["current"] - details["low"]) / details["low"]) * 100, 2
                )
            
            break

try:
    last_save_time = time.time()
    while True:
        start_time = time.time()
        data.run_forever()
        response = data.get_data()
        fetch_time = time.time() - start_time
        # print(f"Data fetch latency: {fetch_time:.4f} seconds")
        
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
