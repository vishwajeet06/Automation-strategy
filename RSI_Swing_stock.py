
import json
import time
import pandas as pd
import talib
from dhanhq import marketfeed
from dhanhq import dhanhq

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

# Fetch historical daily data
def fetch_historical_data(dhan, security_id, exchange_segment, instrument_type, from_date, to_date):
    return dhan.historical_daily_data(security_id, exchange_segment, instrument_type, from_date, to_date)

# Calculate RSI using historical price data
def calculate_rsi(prices, period=7):
    return talib.RSI(pd.Series(prices), timeperiod=period)[-1]

# File path for stock data
file_path = "stock_data.json"
stock_data = load_stock_data(file_path)

from dotenv import load_dotenv
import os
# loaded environment variable
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")
version = "v2"
dhan = dhanhq(client_id, access_token)

# Subscribe to instruments
instruments = get_instruments(stock_data)

data = marketfeed.DhanFeed(client_id, access_token, instruments, version)

historical_data = {}

# Fetch historical data for RSI calculations
from_date = "2025-01-01"  # Modify as needed
to_date = "2025-01-31"
for stock, details in stock_data.items():
    security_id = details["security_token"]
    historical_response = fetch_historical_data(dhan, security_id, marketfeed.NSE, "stock", from_date, to_date)
    print(historical_response)
    if "data" in historical_response:
        historical_data[stock] = {
            "prices": [entry["close"] for entry in historical_response["data"]],
            "volumes": [entry["volume"] for entry in historical_response["data"]]
        }
    else:
        historical_data[stock] = {"prices": [], "volumes": []}

# Update stock data with real-time response
def update_stock_data(response):
    security_id = str(response.get("security_id"))
    for stock, details in stock_data.items():
        if str(details["security_token"]) == security_id:
            details["high"] = float(response.get("high", details["high"]))
            details["low"] = float(response.get("low", details["low"]))
            details["current"] = float(response.get("LTP", details["current"]))
            details["volume"] = int(response.get("volume", details.get("volume", 0)))
            
            if details["low"] > 0:
                details["percent_change_from_low_to_current"] = round(
                    ((details["current"] - details["low"]) / details["low"]) * 100, 2
                )
            
            # Store historical price and volume data
            historical_data[stock]["prices"].append(details["current"])
            historical_data[stock]["volumes"].append(details["volume"])
            
            # Keep only last 20 records
            historical_data[stock]["prices"] = historical_data[stock]["prices"][-20:]
            historical_data[stock]["volumes"] = historical_data[stock]["volumes"][-20:]
            
            # Check swing trading conditions
            if len(historical_data[stock]["prices"]) >= 7:
                rsi_value = calculate_rsi(historical_data[stock]["prices"])
                avg_volume = sum(historical_data[stock]["volumes"]) / len(historical_data[stock]["volumes"])
                
                if rsi_value > 20 and details["volume"] > avg_volume:
                    print(f"Buy Signal: {stock} (RSI: {rsi_value}, Volume: {details['volume']}, Avg Volume: {avg_volume})")
                    # Place Buy Order (to be implemented)
                
                if rsi_value >= 75 or rsi_value < 20 or details["current"] <= details["high"] * 0.94:
                    print(f"Sell Signal: {stock} (RSI: {rsi_value}, Current Price: {details['current']})")
                    # Place Sell Order (to be implemented)
            
            break

try:
    last_save_time = time.time()
    while True:
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
