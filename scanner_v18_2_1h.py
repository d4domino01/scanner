
# V18.2 Matching 1H Stock Scanner (Last Closed Candle)
# Matches TradingView logic: EMA trend + pullback + strong bull candle
# Timeframe: 1H

import yfinance as yf
import pandas as pd

TICKERS = [
    "AAPL","MSFT","NVDA","AMZN","META","TSLA","GOOGL","AMD","NFLX","AVGO",
    "JPM","BAC","XOM","CVX","KO","PEP","MCD","COST","HD","LOW",
    "WMT","DIS","NKE","CAT","GE","BA","UNH","JNJ","PFE","ABBV",
    "ORCL","CRM","ADBE","INTC","CSCO","QCOM","TXN","MU","IBM","SPY",
    "QQQ","IWM","SMH","XLK","XLF","XLE","XLV","XLY","DIA","PANW"
]

def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

signals = []

for ticker in TICKERS:
    try:
        df = yf.download(ticker, period="60d", interval="1h", progress=False)

        if df.empty or len(df) < 30:
            continue

        df["emaFast"] = ema(df["Close"], 9)
        df["emaSlow"] = ema(df["Close"], 21)

        last = df.iloc[-1]

        trendUp = last["emaFast"] > last["emaSlow"] and last["Close"] > last["emaSlow"]

        pullback = last["Low"] <= last["emaFast"]

        body = abs(last["Close"] - last["Open"])
        rng = last["High"] - last["Low"]
        strongBull = last["Close"] > last["Open"] and body >= 0.5 * rng

        if trendUp and pullback and strongBull:
            signals.append({
                "Ticker": ticker,
                "Close": round(last["Close"],2),
                "EMA9": round(last["emaFast"],2),
                "EMA21": round(last["emaSlow"],2)
            })
            print(f"{ticker}: SIGNAL")

    except Exception as e:
        print(f"{ticker}: error {e}")

if signals:
    out = pd.DataFrame(signals)
    out.to_csv("signals.csv", index=False)
    print("\nSignals saved to signals.csv")
else:
    print("\nNo V18.2 signals on last closed 1H candle.")
