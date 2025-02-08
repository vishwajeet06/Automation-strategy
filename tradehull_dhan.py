
from Dhan_Tradehull import Tradehull
import talib
import pandas as pd

from dotenv import load_dotenv
import os
# loaded environment variable
load_dotenv()
client_code = os.getenv("CLIENT_ID")
token_id = os.getenv("ACCESS_TOKEN")
tsl = Tradehull(client_code, token_id)

stockList = ["ABB"]
rsi = 0
for stock in stockList:
    chart = tsl.get_historical_data(stock,"NSE", "DAY")
    last_row_intraday = chart.iloc[[-1]]
    print(last_row_intraday)
    print(chart)
    # chart_intraday = tsl.get_intraday_data(stock,"NSE",5)
    # print(chart_intraday)
    rsi = talib.RSI(chart["close"],7)
    print(rsi[10])



