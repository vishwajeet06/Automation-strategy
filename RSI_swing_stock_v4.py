import json
import time
import asyncio
import threading
import pandas as pd
import talib
import os
from dhanhq import marketfeed
from Dhan_Tradehull import Tradehull
from dotenv import load_dotenv
from telegram import Bot

# Load environment variables
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")
telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
version = "v2"

# File path for stock data
file_path = "stock_data.json"

# Initialize Telegram bot
bot = Bot(token=telegram_token)

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
            chart_daily = await asyncio.to_thread(tsl.get_historical_data, stock, "NSE", "DAY")
            chart_intraday = await asyncio.to_thread(tsl.get_intraday_data, stock, "NSE", 5)
            
            if chart_daily.empty or chart_intraday.empty:
                return  # Skip processing if no data

            # Append last intraday row to daily data
            last_row_intraday = chart_intraday.iloc[[-1]]
            chart_daily = pd.concat([chart_daily, last_row_intraday], ignore_index=True)

            # Calculate RSI
            rsi = talib.RSI(pd.Series(chart_daily["close"]).dropna(), 7)
            rsi_cache[stock] = round(rsi.iloc[-1], 2)  # Cache latest RSI value
            
            # Track RSI min/max for today's data
            today_rsi = rsi.iloc[-20:]  # Last 20 candles as today's data
            min_rsi = today_rsi.min()
            max_rsi = today_rsi.max()
            
            stock_data[stock]["min_rsi_today"] = min_rsi
            stock_data[stock]["max_rsi_today"] = max_rsi
            
            print(f"Updated RSI for {stock}: {rsi_cache[stock]}")
        except Exception as e:
            print(f"Error fetching RSI for {stock}: {e}")

# Background async function to fetch RSI data
async def update_rsi_values():
    tsl = Tradehull(ClientCode=client_id, token_id=access_token)
    semaphore = asyncio.Semaphore(10)

    while True:
        print("Fetching RSI data...")
        start_time = time.time()
        stocks = list(stock_data.keys())

        for i in range(0, len(stocks), 10):
            batch = stocks[i:i + 10]
            tasks = [fetch_stock_data(stock, tsl, semaphore) for stock in batch]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)  # Rate limit buffer

        total_time = time.time() - start_time
        print(f"RSI data updated in {total_time:.2f} seconds.")
        await asyncio.sleep(600)  # Run every hour

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

# Check stocks meeting entry criteria
def check_entry_conditions():
    selected_stocks = set()
    for stock, details in stock_data.items():
        try:
            rsi = details.get("rsi", "N/A")
            min_rsi = details.get("min_rsi_today", 100)
            max_rsi = details.get("max_rsi_today", 0)
            volume = details.get("total_buy_quantity", 0)
            avg_volume = details.get("total_sell_quantity", 1)  # Prevent div/zero
            
            if rsi != "N/A" and min_rsi < 20 and max_rsi > 20 and volume > avg_volume:
                selected_stocks.add(stock)
        except Exception as e:
            print(f"Error checking entry for {stock}: {e}")
    return selected_stocks

# Send Telegram alert
def send_telegram_alert():
    stocks = check_entry_conditions()
    if stocks:
        message = "Stocks meeting RSI criteria:\n" + "\n".join(stocks)
        bot.send_message(chat_id=chat_id, text=message)

# Schedule Telegram alerts every hour
def start_telegram_alerts():
    while True:
        send_telegram_alert()
        time.sleep(3600)

telegram_thread = threading.Thread(target=start_telegram_alerts, daemon=True)
telegram_thread.start()

# WebSocket update function
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
            details["rsi"] = rsi_cache.get(stock, "N/A")
            if details["low"] > 0:
                details["percent_change_from_low_to_current"] = round(
                    ((details["current"] - details["low"]) / details["low"]) * 100, 2
                )
            break

import time
while True:
    try:
        print("Connecting to Dhan WebSocket...")
        data.run_forever()
    except Exception as e:
        print(f"WebSocket error: {e}")
        time.sleep(5)  # Wait before reconnecting

    asyncio.run(data.disconnect())





