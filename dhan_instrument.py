import json
from dhanhq import marketfeed

def get_instruments_from_json(json_file):
    """
    Reads stock_data.json and generates instruments list for subscription.

    :param json_file: Path to stock_data.json
    :return: List of tuples in the format (marketfeed.NSE, security_token, marketfeed.Quote)
    """
    instruments = []

    try:
        with open(json_file, "r") as file:
            stock_data = json.load(file)

        # Iterate over dictionary keys (stock symbols)
        for stock_symbol, stock_info in stock_data.items():
            security_token = stock_info.get("security_token")
            if security_token is not None:
                instruments.append((marketfeed.NSE, str(security_token), marketfeed.Quote))

    except Exception as e:
        print(f"Error reading JSON file: {e}")

    return instruments

# Example usage
json_file_path = "stock_data.json"
instruments_list = get_instruments_from_json(json_file_path)
print(instruments_list)  # Check the output
