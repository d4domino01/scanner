
# V18.2 Matching Scanner — Top 50 Liquid Stocks (30-Min)

This scanner matches the TradingView Pine Script V18.2 logic on a 30-minute timeframe.

## Rules
- EMA(9) > EMA(21)
- Close > EMA(21)
- Low <= EMA(9)
- Close > Open
- Candle body >= 50% of candle range

## Install
pip install -r requirements.txt

## Run
python scanner.py

Notes:
- Scanner checks only last CLOSED 30-min candle.
- Use TradingView 30m timeframe for matching.
