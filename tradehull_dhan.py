import json
from Dhan_Tradehull import Tradehull
import ta
import talib
import pandas as pd
from dotenv import load_dotenv
import os
import time  # To avoid API rate limits

# Load environment variables
load_dotenv()
client_code = os.getenv("CLIENT_ID")
token_id = os.getenv("ACCESS_TOKEN")
tsl = Tradehull(client_code, token_id)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Stock list to test
# stockList = ["ABB", "ACC", "INVALID_SYMBOL"]  # Testing with an invalid symbol
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
    
# Load stock data
stock_data = load_stock_data(file_path)

for stock, details in stock_data.items():
    try:
        chart = tsl.get_historical_data(stock, "NSE", "DAY")

        # 🛑 Check if `chart` is None or empty before proceeding
        if chart is None or chart.empty:
            print(f"⚠️ Skipping {stock}: No data returned")
            continue

        # **TA-Lib RSI (Wilders Smoothing)**
        rsi_talib = talib.RSI(chart["close"], timeperiod=7)

        # **Pandas TA RSI**
        rsi_ta = ta.momentum.RSIIndicator(chart["close"], window=7).rsi()

        # If RSI is below 22, print the stock name
        if rsi_ta.iloc[-1] < 22 or rsi_talib.iloc[-1] < 22:
            print(f"🟢 {stock} RSI < 22 (Pandas: {rsi_ta.iloc[-1]}, TA-Lib: {rsi_talib.iloc[-1]})")
            message = f"🟢 {stock} RSI < 22 (Pandas: {rsi_ta.iloc[-1]}, TA-Lib: {rsi_talib.iloc[-1]})"
            tsl.send_telegram_alert(message,receiver_chat_id=TELEGRAM_CHAT_ID,bot_token=TELEGRAM_BOT_TOKEN)

        # 🕒 Small delay to avoid hitting API rate limits
        time.sleep(0.5)

    except Exception as e:
        print(f"❌ Error processing {stock}: {e}")

