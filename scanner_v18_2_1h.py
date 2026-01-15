import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# =========================
# SETTINGS
# =========================

TIMEFRAME = "15m"
LOOKBACK_DAYS = "7d"

WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA",
    "GOOGL", "AMD", "NFLX", "AVGO", "INTC"
]

# =========================
# FUNCTIONS
# =========================

def get_data(ticker):
    df = yf.download(ticker, period=LOOKBACK_DAYS, interval=TIMEFRAME, progress=False)
    if len(df) < 50:
        return None

    df["ema9"] = ta.trend.ema_indicator(df["Close"], window=9)
    df["ema21"] = ta.trend.ema_indicator(df["Close"], window=21)
    df["atr"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14)

    return df.dropna()


def classify_stock(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    ema_fast = last["ema9"]
    ema_slow = last["ema21"]
    close = last["Close"]
    low = last["Low"]
    open_ = last["Open"]

    atr = last["atr"]

    # ===== TREND FILTER =====
    trend_up = ema_fast > ema_slow and close > ema_slow
    ema_slope_up = ema_fast > prev["ema9"]

    # ===== OVEREXTENSION =====
    ema_dist_pct = (close - ema_fast) / close * 100
    overextended = ema_dist_pct > 1.2

    # ===== EMA ZONE RETEST =====
    ema_zone_retest = (
        (low <= ema_fast and low >= ema_slow) or
        (low <= ema_slow and close > ema_slow)
    )

    # ===== BULLISH RECLAIM =====
    bullish_reclaim = close > open_ and close > ema_fast

    strong_trend = trend_up and ema_slope_up

    # ===== CATEGORIES =====

    if strong_trend and not overextended and ema_zone_retest and bullish_reclaim:
        return "BUY"

    if strong_trend and overextended:
        return "WAIT"

    return "NO TRADE"


# =========================
# SPY MARKET FILTER
# =========================

spy_df = get_data("SPY")
market_ok = False

if spy_df is not None:
    spy_last = spy_df.iloc[-1]
    market_ok = spy_last["Close"] > spy_last["ema21"]

# =========================
# STREAMLIT UI
# =========================

st.set_page_config(layout="wide")
st.title("🔥 V18.2 Trend Pullback Scanner — 15m (Confirmed Entry Logic)")
st.caption("BUY = confirmed execution | WAIT = strong trend but extended | NO TRADE = skip")

st.write(f"📊 **Market Filter (SPY > EMA21):** {'✅ OK' if market_ok else '❌ WEAK — NO BUY SIGNALS'}")

buy_list = []
wait_list = []
no_trade_list = []

for ticker in WATCHLIST:
    df = get_data(ticker)
    if df is None:
        continue

    category = classify_stock(df)

    if category == "BUY" and market_ok:
        buy_list.append(ticker)
    elif category == "WAIT":
        wait_list.append(ticker)
    else:
        no_trade_list.append(ticker)

# =========================
# DISPLAY
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🟢 BUY NOW")
    if buy_list:
        for t in buy_list:
            st.success(t)
    else:
        st.write("empty")

with col2:
    st.subheader("🟡 TRENDING (WAIT)")
    if wait_list:
        for t in wait_list:
            st.warning(t)
    else:
        st.write("empty")

with col3:
    st.subheader("🔴 NO TRADE")
    if no_trade_list:
        for t in no_trade_list:
            st.info(t)
    else:
        st.write("empty")

st.caption("Logic aligned with TradingView V18.2 confirmed ENTRY triangles (15m timeframe)")
