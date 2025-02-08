import datetime
# # from Dhan_Tradehull import Tradehull
# from dhanhq import dhanhq, marketfeed
# from dotenv import load_dotenv
# import os
# # loaded environment variable
# load_dotenv()
# client_id = os.getenv("CLIENT_ID")
# access_token = os.getenv("ACCESS_TOKEN")
# # tsl = Tradehull(Clientcode= access_token, token_id=access_token)

# dhan = dhanhq(access_token, client_id)
# print(dhan)
from_date= datetime.datetime.now()-datetime.timedelta(days=30)
from_date = from_date.strftime('%Y-%m-%d')
to_date = datetime.datetime.now().strftime('%Y-%m-%d')
# # chart = dhan.historical_daily_data(security_id,exchange_segment,instrument_type,expiry_code,from_date,to_date)
# chart = dhan.historical_daily_data(security_id="13",exchange_segment=marketfeed.NSE,instrument_type="EQUITY",from_date=from_date,to_date=to_date)
# print(chart)

import http.client

conn = http.client.HTTPSConnection("api.dhan.co")

# payload = "{\n  \"securityId\": \"13\",\n  \"exchangeSegment\": \"NSE_EQ\",\n  \"instrument\": \"EQUITY\",\n  \"fromDate\": \"2019-08-10\",\n  \"toDate\": \"2019-08-24\"\n}"
payload= {
  "securityId": "13",
  "exchangeSegment": "NSE_EQ",
  "instrument": "EQUITY",
  "fromDate": from_date,
  "toDate": to_date
}

headers = {
    'access-token': "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzQwNzc0MjM0LCJ0b2tlbkNvbnN1bWVyVHlwZSI6IlNFTEYiLCJ3ZWJob29rVXJsIjoiIiwiZGhhbkNsaWVudElkIjoiMTEwMjE0NDM3MSJ9.S7xN9JKAzWKpiDIAU4ge4YN-ASdKyEkaJC4Gwk_gxTapQTxNqe9oAjmCKf_MRxz0nGEdGXwAxyA0ivyB6CsnUw",
    'Content-Type': "application/json",
    'Accept': "application/json"
}

conn.request("POST", "/v2/charts/historical", payload, headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))
