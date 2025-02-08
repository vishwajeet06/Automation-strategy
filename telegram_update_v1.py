
import datetime
import requests
import os
from datetime import datetime, timedelta, timezone
import json
import time
from dhanhq import marketfeed
# Dhan API credentials
from dotenv import load_dotenv
import os


# loaded environment variable
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")
# Load Telegram credentials from environment variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Function to send Telegram messages
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Telegram message sent successfully.")
        else:
            print(f"Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def is_within_trading_hours():
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist).time()
    start_time = datetime.strptime("10:00", "%H:%M").time()
    end_time = datetime.strptime("14:30", "%H:%M").time()
    return start_time <= now <= end_time


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


version = "v2"

# Subscribe to instruments
instruments = get_instruments(stock_data)

data = marketfeed.DhanFeed(client_id, access_token, instruments, version)

def update_stock_data(response):
    security_id = str(response.get("security_id"))
    for stock, details in stock_data.items():
        # print(response)
        if str(details["security_token"]) == security_id:
            details["high"] = float(response.get("high", details["high"]))
            details["low"] = float(response.get("low", details["low"]))
            details["open"] = float(response.get("open", details.get("open", 0)))
            details["current"] = float(response.get("LTP", details["current"]))
            if details["low"] > 0:
                details["percent_change_from_low_to_current"] = round(
                    ((details["current"] - details["low"]) / details["low"]) * 100, 2
                )
            
            # Check if the stock meets the new condition
            if is_within_trading_hours():
                if 2.5 <= details["percent_change_from_low_to_current"] <= 3 and details["current"] > details["open"]:
                    message = f"Stock Alert: {stock}\nPrice: {details['current']}\nOpen: {details['open']}\nChange: {details['percent_change_from_low_to_current']}%"
                    # print(message)
                    # send_telegram_message(message)
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
