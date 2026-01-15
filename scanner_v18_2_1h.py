import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import webbrowser
from datetime import datetime

# ======================
# CONFIG
# ======================
TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","JPM","XOM",
    "V","PG","MA","AVGO","COST","PEP","KO","WMT","HD","LLY",
    "MRK","ABBV","CRM","NFLX","ADBE","ORCL","AMD","INTC","QCOM","TXN",
    "AMAT","GE","CAT","BA","DE","GS","MS","BAC","SPY","QQQ",
    "IWM","DIA","XLK","XLF","XLE","XLV","XLY"
]

EMA_FAST = 9
EMA_SLOW = 21
ATR_LEN = 14

# ======================
# UI
# ======================
st.set_page_config(layout="wide")
st.title("📈 V18.2 Trend Pullback Scanner — TradingView Linked")

tf = st.selectbox("Timeframe", ["30m", "1h"])
interval = "30m" if tf == "30m" else "60m"
period = "7d" if tf == "30m" else "14d"

st.caption("Signal logic IDENTICAL to your working V18.2 scanner")

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

def tv_link(ticker, tf):
    interval = "60" if tf == "1h" else "30"
    return f"https://www.tradingview.com/chart/?symbol={ticker}&interval={interval}"

# ======================
# SCAN
# ======================
buy_rows = []
setup = []
trending = []

with st.spinner("Scanning market..."):

    for ticker in TICKERS:
        try:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if len(df) < 50:
                continue

            df["EMA9"] = ema(df["Close"], 9)
            df["EMA21"] = ema(df["Close"], 21)
            df["ATR"] = atr(df, ATR_LEN)
            df["ATR_AVG"] = df["ATR"].rolling(20).mean()

            last = df.iloc[-1]
            prev = df.iloc[-2]

            # ===== ORIGINAL V18.2 LOGIC (UNCHANGED) =====
            trend_up = last["EMA9"] > last["EMA21"] and last["Close"] > last["EMA21"]
            ema_slope = last["EMA9"] > prev["EMA9"]
            vol_ok = last["ATR"] > last["ATR_AVG"] * 0.8

            pullback_zone = last["Low"] <= last["EMA9"] + last["ATR"] * 0.1
            bullish = last["Close"] > last["Open"]
            pullback = pullback_zone and bullish and last["Close"] > last["EMA9"]

            # ===== SCORE (DISPLAY ONLY) =====
            score = 0
            score += min((last["EMA9"] - last["EMA21"]) / last["Close"] * 500, 30)
            score += min((last["EMA9"] - prev["EMA9"]) / last["Close"] * 800, 25)
            score += min((last["ATR"] / last["ATR_AVG"]) * 20, 25)
            score += 20 if pullback else 0

            stop = last["EMA9"] - last["ATR"] * 1.2

            if trend_up and ema_slope and vol_ok and pullback:
                buy_rows.append([
                    ticker,
                    round(score,1),
                    round(last["Close"],2),
                    round(stop,2),
                    tv_link(ticker, tf)
                ])

            elif trend_up and ema_slope and pullback_zone:
                setup.append((ticker, tv_link(ticker, tf)))

            elif trend_up and ema_slope:
                trending.append((ticker, tv_link(ticker, tf)))

        except:
            pass

# ======================
# DISPLAY
# ======================
st.subheader("🟢 BUY NOW — Ranked")

if buy_rows:
    df_buy = pd.DataFrame(buy_rows, columns=["Ticker","Score","Entry","Stop","Chart"])
    df_buy = df_buy.sort_values("Score", ascending=False)
    st.dataframe(df_buy, use_container_width=True)

    top = df_buy.iloc[0]["Chart"]
    if "last_opened" not in st.session_state or st.session_state["last_opened"] != top:
        webbrowser.open_new_tab(top)
        st.session_state["last_opened"] = top
else:
    st.write("No BUY setups right now")

c1, c2 = st.columns(2)

with c1:
    st.subheader("🟡 SETUP (forming)")
    for t, link in setup:
        st.markdown(f"- [{t}]({link})")
    if not setup:
        st.write("None")

with c2:
    st.subheader("🔵 TRENDING")
    for t, link in trending:
        st.markdown(f"- [{t}]({link})")
    if not trending:
        st.write("None")

st.caption(f"Scan time: {datetime.now().strftime('%H:%M:%S')} | TF: {tf}")
