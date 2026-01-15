import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("V18.2 Hybrid ORB + Trend Pullback Scanner (1H)")

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

def add_indicators(df):
    df["ema_fast"] = df["Close"].ewm(span=EMA_FAST).mean()
    df["ema_slow"] = df["Close"].ewm(span=EMA_SLOW).mean()

    tr = pd.concat([
        df["High"] - df["Low"],
        abs(df["High"] - df["Close"].shift()),
        abs(df["Low"] - df["Close"].shift())
    ], axis=1).max(axis=1)

    df["atr"] = tr.rolling(ATR_LEN).mean()
    df["atr_avg"] = df["atr"].rolling(ATR_AVG_LEN).mean()

    return df


def get_orb_levels(df):
    df = df.copy()
    df["date"] = df.index.date

    today = df["date"].iloc[-1]
    day_df = df[df["date"] == today]

    if len(day_df) < 1:
        return None, None, False

    bars_needed = int((ORB_MINUTES * 60) / 3600)

    orb_df = day_df.iloc[:bars_needed]

    if len(orb_df) < bars_needed:
        return None, None, False

    return orb_df["High"].max(), orb_df["Low"].min(), True


def check_signal(df):
    df = df.dropna()
    last = df.iloc[-1]
    prev = df.iloc[-2]

    or_high, or_low, orb_done = get_orb_levels(df)

    # === Trend filter ===
    trend_up = last["ema_fast"] > last["ema_slow"] and last["Close"] > last["ema_slow"]
    ema_slope_up = last["ema_fast"] > prev["ema_fast"]

    # === Volatility filter ===
    vol_ok = last["atr"] > last["atr_avg"] * 0.8

    # === Pullback ===
    pullback = (
        last["Low"] <= last["ema_fast"] + (last["atr"] * 0.1)
        and last["Close"] > last["ema_fast"]
        and last["Close"] > last["Open"]
    )

    # === ORB breakout ===
    orb_breakout = orb_done and or_high is not None and last["Close"] > or_high

    buy = trend_up and ema_slope_up and vol_ok and (pullback or orb_breakout)

    near = trend_up and vol_ok and abs(last["Close"] - last["ema_fast"]) < last["atr"] * 0.25

    return buy, near


# =============================
# SCANNER
# =============================

results = []

progress = st.progress(0)

for i, ticker in enumerate(TICKERS):
    try:
        df = yf.download(
            ticker,
            period="10d",
            interval="1h",
            progress=False
        )

        if df is None or len(df) < 50:
            continue

        df = add_indicators(df)

        buy, near = check_signal(df)

        if buy:
            status = "BUY"
        elif near:
            status = "NEAR"
        else:
            status = "NO TRADE"

        # >>> ONLY ADDITION: SIGNAL TIME FROM LAST CANDLE <<<
        signal_time = df.index[-1].strftime("%Y-%m-%d %H:%M")

        results.append({
            "Ticker": ticker,
            "Signal": status,
            "Price": round(df["Close"].iloc[-1], 2),
            "Time": signal_time
        })

    except Exception as e:
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
    st.subheader("BUY NOW")
    st.dataframe(df_out[df_out["Signal"] == "BUY"])

with col2:
    st.subheader("NEAR SETUP")
    st.dataframe(df_out[df_out["Signal"] == "NEAR"])

with col3:
    st.subheader("NO TRADE")
    st.dataframe(df_out[df_out["Signal"] == "NO TRADE"])

st.caption("Logic aligned with V18.2 Hybrid ORB + Trend Pullback (1H)")
