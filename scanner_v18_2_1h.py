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
st.title("📈 V18.2 Trend Pullback Scanner — 4 Levels")

tf = st.selectbox("Timeframe", ["30m", "1h"])
st.caption("Same logic as TradingView V18.2 — strict pullback only")

# ======================
# DATA
# ======================
interval = "30m" if tf == "30m" else "60m"
period = "7d" if tf == "30m" else "14d"

buy_now = []
setup = []
trending = []
no_trade = []

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
with st.spinner("Scanning market..."):

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
            prev = df.iloc[-2]

            # === V18.2 CONDITIONS ===
            trend_up = last["EMA_FAST"] > last["EMA_SLOW"] and last["Close"] > last["EMA_SLOW"]
            ema_slope = last["EMA_FAST"] > prev["EMA_FAST"]
            vol_ok = last["ATR"] > last["ATR_AVG"] * 0.8

            pullback_zone = last["Low"] <= last["EMA_FAST"] + last["ATR"] * 0.1
            bullish = last["Close"] > last["Open"]

            pullback = pullback_zone and bullish and last["Close"] > last["EMA_FAST"]

            if trend_up and ema_slope and vol_ok and pullback:
                buy_now.append(ticker)

            elif trend_up and ema_slope and pullback_zone:
                setup.append(ticker)

            elif trend_up and ema_slope:
                trending.append(ticker)

            else:
                no_trade.append(ticker)

        except:
            pass

# ======================
# DISPLAY
# ======================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.subheader("🟢 BUY NOW")
    for t in buy_now:
        st.success(t)
    if not buy_now:
        st.write("None")

with c2:
    st.subheader("🟡 SETUP")
    for t in setup:
        st.warning(t)
    if not setup:
        st.write("None")

with c3:
    st.subheader("🔵 TRENDING")
    for t in trending:
        st.info(t)
    if not trending:
        st.write("None")

with c4:
    st.subheader("🔴 NO TRADE")
    for t in no_trade[:10]:
        st.write(t)
    if not no_trade:
        st.write("None")

st.caption(f"Scan time: {datetime.now().strftime('%H:%M:%S')} | TF: {tf}")
