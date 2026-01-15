import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ======================
# CONFIG
# ======================
TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","BRK-B","JPM",
    "UNH","XOM","V","PG","MA","AVGO","COST","PEP","KO","WMT",
    "HD","LLY","MRK","ABBV","CRM","NFLX","ADBE","ORCL","AMD","INTC",
    "QCOM","TXN","AMAT","GE","CAT","BA","DE","GS","MS","BAC",
    "SPY","QQQ","IWM","DIA","XLK","XLF","XLE","XLV","XLY"
]

EMA_FAST = 9
EMA_SLOW = 21
ATR_LEN = 14

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📈 V18.2 Trend Pullback Scanner")

tf = st.selectbox("Timeframe", ["30m", "1h"])
refresh = st.button("🔄 Refresh Now")

st.write("BUY = pullback in trend | TRENDING = strong trend, waiting for pullback")

# ======================
# DATA
# ======================
interval = "30m" if tf == "30m" else "60m"
period = "7d" if tf == "30m" else "14d"

buy_list = []
trend_list = []

# ======================
# FUNCTIONS
# ======================
def ema(series, n):
    return series.ewm(span=n, adjust=False).mean()

def atr(df, n):
    tr = pd.concat([
        df["High"] - df["Low"],
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()

# ======================
# SCAN
# ======================
with st.spinner("Scanning..."):

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if len(df) < 50:
                continue

            df["EMA_FAST"] = ema(df["Close"], EMA_FAST)
            df["EMA_SLOW"] = ema(df["Close"], EMA_SLOW)
            df["ATR"] = atr(df, ATR_LEN)
            df["ATR_AVG"] = df["ATR"].rolling(20).mean()

            last = df.iloc[-1]

            # === V18.2 LOGIC ===
            trend_up = last["EMA_FAST"] > last["EMA_SLOW"] and last["Close"] > last["EMA_SLOW"]
            ema_slope = df["EMA_FAST"].iloc[-1] > df["EMA_FAST"].iloc[-2]
            vol_ok = last["ATR"] > last["ATR_AVG"] * 0.8

            pullback = (
                last["Low"] <= last["EMA_FAST"] + last["ATR"] * 0.1 and
                last["Close"] > last["EMA_FAST"] and
                last["Close"] > last["Open"]
            )

            if trend_up and ema_slope and vol_ok and pullback:
                buy_list.append(ticker)

            elif trend_up and ema_slope:
                trend_list.append(ticker)

        except:
            pass

# ======================
# DISPLAY
# ======================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🟢 BUY (Pullback Entry)")
    if buy_list:
        for t in buy_list:
            st.success(t)
    else:
        st.write("No BUY setups right now")

with col2:
    st.subheader("🟡 TRENDING (Wait for Pullback)")
    if trend_list:
        for t in trend_list:
            st.warning(t)
    else:
        st.write("No trending stocks right now")

st.caption(f"Last scan: {datetime.now().strftime('%H:%M:%S')} | Timeframe: {tf}")
