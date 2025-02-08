
from dhanhq import dhanhq
import pandas as pd


from dotenv import load_dotenv
import os
# loaded environment variable
load_dotenv()
client_id = os.getenv("CLIENT_ID")
access_token = os.getenv("ACCESS_TOKEN")

# print(client_id)

dhan = dhanhq(client_id, access_token)
# dhan = dhanhq(client_id,access_token)
print(dhan.quote_data(securities = {"NSE_EQ":[13]}))

# get holdings
holdings = dhan.get_fund_limits()
print(holdings['data']['availabelBalance'])

data = dhan.ticker_data( securities = {
                    "NSE_EQ": [17875]
                })
print(data)
print(data['data']['data']['NSE_EQ']['17875']['last_price'])

# from_date = "2025-01-01"  # Modify as needed
# to_date = "2025-01-30"


# historical_response = dhan.historical_daily_data(security_id="17875", exchange_segment="NSE_EQ", instrument_type="EQUITY", from_date=from_date, to_date=to_date)
# print(historical_response)