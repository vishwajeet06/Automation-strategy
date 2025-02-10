import time
import numpy as np
import pandas as pd
import numba as nb
import ta
import vectorbt as vbt
from Dhan_Tradehull import Tradehull
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
client_code = os.getenv("CLIENT_ID")
token_id = os.getenv("ACCESS_TOKEN")
tsl = Tradehull(client_code, token_id)

# Numba RSI function (fastest method)
@nb.jit(nopython=True)
def rsi_numba(close, period=14):
    deltas = np.diff(close)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.empty_like(close)
    avg_loss = np.empty_like(close)
    avg_gain[:period] = gains[:period].mean()
    avg_loss[:period] = losses[:period].mean()

    for i in range(period, len(close)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Stock to test
stock = "INFY"

# Fetch historical data
chart = tsl.get_historical_data(stock, "NSE", "DAY")
if chart is None or "close" not in chart:
    print(f"Error fetching data for {stock}")
    exit()

close_prices = chart["close"].values


# **Method 2: Vectorbt RSI**
start_time = time.time()
rsi_vectorbt = vbt.IndicatorFactory.from_pandas_ta('rsi').run(close_prices, 7).rsi
vectorbt_time = time.time() - start_time

# **Method 1: Numba RSI (Fastest)**
start_time = time.time()
rsi_numba_values = rsi_numba(close_prices, period=7)
numba_time = time.time() - start_time

# **Method 3: Pandas TA RSI**
start_time = time.time()
rsi_ta = ta.momentum.RSIIndicator(pd.Series(close_prices), window=7).rsi()
pandas_ta_time = time.time() - start_time

# Print RSI values & execution times
print(f"\nRSI Comparison for {stock}:")
print(f"Vectorbt RSI: {rsi_vectorbt.iloc[-1]:.2f} (Time: {vectorbt_time:.6f} sec)")
print(f"Pandas TA RSI: {rsi_ta.iloc[-1]:.2f} (Time: {pandas_ta_time:.6f} sec)")
print(f"Numba RSI: {rsi_numba_values[-1]:.2f} (Time: {numba_time:.6f} sec)")
