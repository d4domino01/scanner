
"""
V18.2 Matching Scanner — Top 50 Liquid Momentum Stocks (30-Min)

Matches TradingView V18.2 logic exactly, using 30-minute candles.
"""

import yfinance as yf
import pandas as pd
from tickers import TICKERS

EMA_FAST = 9
EMA_SLOW = 21

def compute_signal(symbol):
    df = yf.download(symbol, period="7d", interval="30m", progress=False)
    if df.empty or len(df) < EMA_SLOW + 5:
        return None

    df["EMA9"] = df["Close"].ewm(span=EMA_FAST, adjust=False).mean()
    df["EMA21"] = df["Close"].ewm(span=EMA_SLOW, adjust=False).mean()

    last = df.iloc[-1]

    ema9 = last["EMA9"]
    ema21 = last["EMA21"]
    close = last["Close"]
    open_ = last["Open"]
    low = last["Low"]
    high = last["High"]

    trend_up = ema9 > ema21 and close > ema21
    pullback = low <= ema9 and close > ema21

    body = abs(close - open_)
    rng = max(high - low, 1e-6)
    strong_bull = close > open_ and body >= 0.5 * rng

    if trend_up and pullback and strong_bull:
        strength = body / rng
        return {
            "Ticker": symbol,
            "Time": str(df.index[-1]),
            "Close": round(float(close), 2),
            "EMA9": round(float(ema9), 2),
            "EMA21": round(float(ema21), 2),
            "Strength": round(float(strength), 2)
        }
    return None

def main():
    results = []
    for sym in TICKERS:
        try:
            res = compute_signal(sym)
            if res:
                results.append(res)
        except Exception as e:
            print(f"{sym}: error {e}")

    if not results:
        print("No V18.2 signals found on last closed 30-min candle.")
        return

    df = pd.DataFrame(results).sort_values("Strength", ascending=False)
    print("\nV18.2 Signals (Top Momentum First)\n")
    print(df.to_string(index=False))

    df.to_csv("signals.csv", index=False)
    print("\nSaved to signals.csv")

if __name__ == "__main__":
    main()
