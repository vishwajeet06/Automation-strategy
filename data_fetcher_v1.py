
import json
from dhanhq import marketfeed

# Load stock data
file_path = "stock_data.json"
def load_stock_data():
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading stock data: {e}")
        return {}

# Save stock data
def save_stock_data(data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving stock data: {e}")

# Generate instruments list from stock_data.json
def get_instruments(stock_data):
    instruments = []
    for stock, details in stock_data.items():
        security_id = details.get("security_token")
        if security_id:
            instruments.append((marketfeed.NSE, str(security_id), marketfeed.Quote))
    return instruments

# Update stock data on receiving a response
def update_stock_data(response, stock_data):
    security_id = str(response.get("security_id"))
    for stock, details in stock_data.items():
        if str(details.get("security_token")) == security_id:
            details["high"] = float(response.get("high", details["high"]))
            details["low"] = float(response.get("low", details["low"]))
            details["current"] = float(response.get("LTP", details["current"]))
            details["percent_change_from_low_to_current"] = (
                ((details["current"] - details["low"]) / details["low"]) * 100
                if details["low"] > 0 else 0
            )
    save_stock_data(stock_data)

# Main function to stream data
def start_streaming(client_id, access_token):
    stock_data = load_stock_data()
    instruments = get_instruments(stock_data)
    version = "v2"
    
    try:
        data = marketfeed.DhanFeed(client_id, access_token, instruments, version)
        while True:
            data.run_forever()
            response = data.get_data()
            if response:
                update_stock_data(response, stock_data)
                print(response)
    except Exception as e:
        print(f"Streaming error: {e}")
    finally:
        data.disconnect()

# Run the script with your credentials
if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    # loaded environment variable
    load_dotenv()
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    start_streaming(client_id, access_token)
