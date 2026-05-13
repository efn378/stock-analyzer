import yfinance as yf
import streamlit as st

st.title("Stock Odds Analyzer")

ticker = st.text_input("Enter ticker", "AAPL").upper()

if ticker:
    data = yf.download(ticker, period="20y", auto_adjust=True)

    if data.empty:
        st.error("No data found.")
    else:
        close = data["Close"]

        if hasattr(close, "columns"):
            close = close.iloc[:, 0]

        data["SMA50"] = close.rolling(50).mean()
        data["SMA200"] = close.rolling(200).mean()

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        data["RSI"] = 100 - (100 / (1 + rs))

        latest_close = float(close.iloc[-1])
        latest_sma50 = float(data["SMA50"].iloc[-1])
        latest_sma200 = float(data["SMA200"].iloc[-1])
        latest_rsi = float(data["RSI"].iloc[-1])

        score = 0
        max_score = 6

        if latest_close > latest_sma200:
            score += 2

        if latest_sma50 > latest_sma200:
            score += 2

        if 40 <= latest_rsi <= 70:
            score += 1

        if latest_close > latest_sma50:
            score += 1

        odds_up = round((score / max_score) * 100, 1)

        st.subheader(ticker)
        st.write(f"Current Price: ${latest_close:.2f}")
        st.write(f"RSI: {latest_rsi:.1f}")
        st.write(f"Bullish Score: {score}/{max_score}")
        st.write(f"Estimated Odds Up: {odds_up}%")

        st.line_chart(close)