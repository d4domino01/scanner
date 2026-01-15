import streamlit as st
import yfinance as yf
import pandas as pd
import time

# ---------------- SETTINGS ----------------

TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA",
    "JPM","BAC","WMT","COST","HD","KO","XOM","CVX",
    "PEP","MCD","DIS","NFLX","UNH","LLY"
]

TF = "1h"
FAST_EMA = 9
SLOW_EMA = 21
PULLBACK_PCT = 0.6 # distance to EMA fast

REFRESH_SEC = 300

# ---------------- FUNCTIONS ----------------

def get_data(ticker):
    df = yf.download(ticker, period="10d", interval=TF, progress=False)
    if df.empty or len(df) < 30:
        return None
    return df

def add_indicators(df):
    df["ema_fast"] = df["Close"].ewm(span=FAST_EMA).mean()
    df["ema_slow"] = df["Close"].ewm(span=SLOW_EMA).mean()
    df["hh"] = df["High"].rolling(5).max()
    return df

def classify(df):
    c = df.iloc[-1]
    p1 = df.iloc[-2]
    p2 = df.iloc[-3]

    trend = c["ema_fast"] > c["ema_slow"] and c["Close"] > c["ema_slow"]

    pullback_zone = abs(c["Close"] - c["ema_fast"]) / c["Close"] < (PULLBACK_PCT / 100)
    bullish = c["Close"] > c["Open"]

    buy_now = trend and pullback_zone and bullish

    recent_buy = False
    for bar in [p1, p2]:
        pb = abs(bar["Close"] - bar["ema_fast"]) / bar["Close"] < (PULLBACK_PCT / 100)
        bull = bar["Close"] > bar["Open"]
        if (bar["ema_fast"] > bar["ema_slow"]) and pb and bull:
            recent_buy = True

    trending = (
        trend
        and c["Close"] > c["ema_fast"]
        and c["High"] >= df["hh"].iloc[-1]
        and not pullback_zone
    )

    if buy_now:
        return "BUY NOW"
    elif recent_buy:
        return "RECENT"
    elif trending:
        return "TRENDING"
    else:
        return "NO TRADE"

# ---------------- UI ----------------

st.set_page_config(layout="wide")
st.title("🔥 V18.2 Trend Pullback Scanner — 1H (Auto Refresh)")
st.caption("Auto refresh every 5 minutes | BUY = pullback only | TRENDING = strong trend")

placeholder = st.empty()

while True:

    buy_list = []
    recent_list = []
    trending_list = []
    no_trade_list = []

    for t in TICKERS:
        try:
            df = get_data(t)
            if df is None:
                continue
            df = add_indicators(df)
            status = classify(df)
            price = round(df["Close"].iloc[-1], 2)

            row = {"Ticker": t, "Price": price, "Signal": status}

            if status == "BUY NOW":
                buy_list.append(row)
            elif status == "RECENT":
                recent_list.append(row)
            elif status == "TRENDING":
                trending_list.append(row)
            else:
                no_trade_list.append(row)

        except:
            pass

    with placeholder.container():
        c1, c2, c3, c4 = st.columns(4)

        c1.subheader("🟢 BUY NOW")
        if buy_list:
            c1.dataframe(pd.DataFrame(buy_list), use_container_width=True)
        else:
            c1.write("empty")

        c2.subheader("🟡 TRENDING (WAIT)")
        if trending_list:
            c2.dataframe(pd.DataFrame(trending_list), use_container_width=True)
        else:
            c2.write("empty")

        c3.subheader("🔵 RECENT (≤2H)")
        if recent_list:
            c3.dataframe(pd.DataFrame(recent_list), use_container_width=True)
        else:
            c3.write("empty")

        c4.subheader("🔴 NO TRADE")
        if no_trade_list:
            c4.dataframe(pd.DataFrame(no_trade_list), use_container_width=True)
        else:
            c4.write("empty")

        st.caption("Logic aligned with V18.2 Hybrid ORB + Trend Pullback (1H)")

    time.sleep(REFRESH_SEC)
