import json
import time
import requests
import datetime
from threading import Thread
from dhanhq import marketfeed
from dhanhq import dhanhq
import os

from dotenv import load_dotenv
import os
# loaded environment variable
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")



# dhan = dhanhq(client_id,access_token)
# print(dhan.quote_data(securities = {"NSE_EQ":[13]}))

# Load stock data from the JSON file
def load_stock_data():
    with open("stock_data.json", "r") as file:
        return json.load(file)

# Fetch OHLC data from the Dhan API for a given set of stocks
def fetch_market_data(stock_data):
    url = "https://api.dhan.co/v2/marketfeed/ohlc"
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'access-token': access_token,  # Replace with your access token
        'client-id': client_id,  # Replace with your client id
    }
    
    # Prepare the request body
    nse_eq_stocks = [stock_data[stock]["security_token"] for stock in stock_data]
    # print(nse_eq_stocks)
    request_data = {
        "NSE_EQ": nse_eq_stocks
    }
    response = requests.post(url, headers=headers, json=request_data)
    if response.status_code == 200:
        data = response.json()
        print(data)
        update_stock_data(data, stock_data)
    else:
        print(f"Error fetching data: {response.status_code}")

# Update the in-memory stock data with the latest market data
def update_stock_data(data, stock_data):
    for category in data["data"]:
        for instrument in data["data"][category]:
            stock_id = str(instrument)
            if stock_id in stock_data:
                stock_data[stock_id]["high"] = data["data"][category][stock_id]["ohlc"]["high"]
                stock_data[stock_id]["low"] = data["data"][category][stock_id]["ohlc"]["low"]
                stock_data[stock_id]["current"] = data["data"][category][stock_id]["last_price"]
                stock_data[stock_id]["percent_change_from_low_to_current"] = (
                    (stock_data[stock_id]["current"] - stock_data[stock_id]["low"]) /
                    stock_data[stock_id]["low"] * 100
                )

# Save the updated stock data to a JSON file periodically
def save_to_json(stock_data):
    print(stock_data)
    while True:
        with open("stock_data.json", "w") as file:
            json.dump(stock_data, file, indent=4)
        time.sleep(60)  # Save every minute

# Main function to run the data fetching and saving
def run():
    stock_data = load_stock_data()
    
    while True:
        # Fetch market data and update stock data
        fetch_market_data(stock_data)
        
        # Wait for a minute before the next fetch
        time.sleep(60)

# Start the WebSocket and save data to JSON in separate threads
if __name__ == "__main__":
    save_thread = Thread(target=save_to_json, args=(load_stock_data(),))
    save_thread.start()

    # Start the data fetching process
    run()
