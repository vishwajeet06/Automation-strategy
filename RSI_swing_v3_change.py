import json
import time
import asyncio
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

# Load Telegram credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

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

# Asynchronous function to fetch data for a single stock
async def fetch_stock_data(stock, tsl, semaphore):
    async with semaphore:  # Limit concurrent requests
        try:
            loop = asyncio.get_running_loop()
            
            # Fetch daily and intraday data
            chart_daily = await loop.run_in_executor(None, tsl.get_historical_data, stock, "NSE", "DAY")
            chart_intraday = await loop.run_in_executor(None, tsl.get_intraday_data, stock, "NSE", 5)

            # Append the last row of intraday data to daily data
            last_row_intraday = chart_intraday.iloc[[-1]]
            chart_daily = pd.concat([chart_daily, last_row_intraday], ignore_index=True)

            # Calculate RSI
            rsi = talib.RSI(pd.Series(chart_daily["close"]), 7)
            rsi_cache[stock] = round(rsi.iloc[-1], 2)  # Cache latest RSI value
            print(f"Updated RSI for {stock}: {rsi_cache[stock]}")

            # previous day RSI
            rsi_previous = talib.RSI(chart_daily["close"],5)

            # Send Telegram alert if RSI is between 20 and 25
            if 20 <= rsi_cache[stock] <= 25:
                message = f"RSI Alert: {stock} RSI = {rsi_cache[stock]}"
                tsl.send_telegram_alert(message=message, receiver_chat_id=TELEGRAM_CHAT_ID, bot_token=TELEGRAM_BOT_TOKEN)

        except Exception as e:
            print(f"Error fetching RSI for {stock}: {e}")

# Background async function to fetch RSI data for all stocks
async def update_rsi_values():
    tsl = Tradehull(ClientCode=client_id, token_id=access_token)
    semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent requests

    while True:
        print("Fetching RSI data...")
        start_time = time.time()

        # Fetch data for all stocks in batches of 10
        stocks = list(stock_data.keys())
        for i in range(0, len(stocks), 10):
            batch = stocks[i:i + 10]
            tasks = [fetch_stock_data(stock, tsl, semaphore) for stock in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)  # Wait 1 second between batches

        total_time = time.time() - start_time
        print(f"RSI data updated in {total_time:.2f} seconds.")
        await asyncio.sleep(300)  # Fetch RSI every 5 minutes

# Start the RSI fetching thread
def start_rsi_thread():
    asyncio.run(update_rsi_values())

rsi_thread = threading.Thread(target=start_rsi_thread, daemon=True)
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

            # Assign RSI from cache
            details["rsi"] = rsi_cache.get(stock, "N/A")

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
