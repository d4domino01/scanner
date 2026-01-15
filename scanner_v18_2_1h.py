import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import os

st.set_page_config(layout="wide")
st.title("🔥 V18.2 Hybrid ORB + Trend Pullback Scanner (CONFIRMED ENTRY)")

# =============================
# SETTINGS
# =============================

TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","BAC","WMT",
    "COST","HD","LOW","UNH","LLY","JNJ","PFE","XOM","CVX","KO",
    "PEP","DIS","MCD","SBUX","NFLX","CRM","ORCL","ADBE","INTC","AMD",
    "AVGO","QCOM","TXN","IBM","CAT","GE","BA","MMM","GS","MS",
    "C","AXP","V","MA","PYPL","SHOP","NKE","TGT"
]

EMA_FAST = 9
EMA_SLOW = 21
ATR_LEN = 14
ATR_AVG_LEN = 20
ORB_MINUTES = 30

# =============================
# FUNCTIONS
# =============================

def clean_df(df):
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    return df


def add_indicators(df):
    df["ema_fast"] = df["Close"].ewm(span=EMA_FAST, adjust=False).mean()
    df["ema_slow"] = df["Close"].ewm(span=EMA_SLOW, adjust=False).mean()

    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"] - df["Close"].shift()).abs()
    ], axis=1).max(axis=1)

    df["atr"] = tr.rolling(ATR_LEN).mean()
    df["atr_avg"] = df["atr"].rolling(ATR_AVG_LEN).mean()
    return df


def get_orb_levels(df):
    df = df.copy()
    df["date"] = df.index.date
    today = df["date"].iloc[-1]
    day_df = df[df["date"] == today]

    bars_needed = int(ORB_MINUTES / 60 * len(day_df))

    if len(day_df) < bars_needed or bars_needed < 1:
        return None, None, False

    orb_df = day_df.iloc[:bars_needed]
    return orb_df["High"].max(), orb_df["Low"].min(), True


def check_signal(df):
    df = df.dropna()

    if len(df) < 30:
        return "NO DATA"

    last = df.iloc[-1]
    prev = df.iloc[-2]

    or_high, or_low, orb_done = get_orb_levels(df)

    trend_up = last["ema_fast"] > last["ema_slow"] and last["Close"] > last["ema_slow"]
    ema_slope_up = last["ema_fast"] > prev["ema_fast"]

    vol_ok = last["atr"] > last["atr_avg"] * 0.8

    ema_zone = (
        (last["Low"] <= last["ema_fast"] and last["Low"] >= last["ema_slow"]) or
        (last["Low"] <= last["ema_slow"] and last["Close"] > last["ema_slow"])
    )

    bullish_reclaim = last["Close"] > last["Open"] and last["Close"] > last["ema_fast"]

    ema_dist = abs(last["Close"] - last["ema_fast"]) / last["Close"] * 100
    overextended = ema_dist > 1.2

    orb_breakout = orb_done and or_high is not None and last["Close"] > or_high

    base_long = trend_up and ema_slope_up and vol_ok and (ema_zone or orb_breakout)

    if base_long and bullish_reclaim and not overextended:
        return "BUY"

    if trend_up and not bullish_reclaim:
        return "TRENDING (WAIT)"

    return "NO TRADE"


# =============================
# SCANNER
# =============================

results = []
progress = st.progress(0)

for i, ticker in enumerate(TICKERS):
    try:
        df = yf.download(ticker, period="10d", interval="1h", progress=False)
        df = clean_df(df)

        if df is None or len(df) < 50:
            continue

        df = add_indicators(df)
        signal = check_signal(df)

        signal_time = df.index[-1].strftime("%H:%M")
        price = round(df["Close"].iloc[-1], 2)

        results.append({
            "Ticker": ticker,
            "Signal": signal,
            "Price": price,
            "Time": signal_time
        })

    except Exception:
        results.append({
            "Ticker": ticker,
            "Signal": "ERROR",
            "Price": "-",
            "Time": "-"
        })

    progress.progress((i + 1) / len(TICKERS))


# =============================
# OUTPUT
# =============================

df_out = pd.DataFrame(results)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🟢 BUY NOW")
    st.dataframe(df_out[df_out["Signal"] == "BUY"], use_container_width=True)

with col2:
    st.subheader("🟡 TRENDING (WAIT)")
    st.dataframe(df_out[df_out["Signal"] == "TRENDING (WAIT)"], use_container_width=True)

with col3:
    st.subheader("🔴 NO TRADE")
    st.dataframe(df_out[df_out["Signal"] == "NO TRADE"], use_container_width=True)

st.caption("Logic aligned with TradingView V18.2 CONFIRMED ENTRY triangles (EMA retest + bullish reclaim)")
