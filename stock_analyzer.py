import yfinance as yf
import streamlit as st
import pandas as pd

st.title("Stock Odds Analyzer")

# ---------- SINGLE STOCK ANALYZER ----------

st.header("Single Stock Analysis")

ticker = st.text_input("Enter ticker", "AAPL").upper()

def calculate_score(ticker):
    try:
        data = yf.download(ticker, period="20y", auto_adjust=True, progress=False)

        if data.empty:
            return None

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

        if latest_close > latest_sma200:
            score += 2

        if latest_sma50 > latest_sma200:
            score += 2

        if 40 <= latest_rsi <= 70:
            score += 1

        if latest_close > latest_sma50:
            score += 1

        odds_up = round((score / 6) * 100, 1)

        return {
            "ticker": ticker,
            "price": latest_close,
            "rsi": latest_rsi,
            "score": score,
            "odds": odds_up,
            "chart": close
        }

    except:
        return None

if ticker:
    result = calculate_score(ticker)

    if result:
        st.subheader(result["ticker"])
        st.write(f"Current Price: ${result['price']:.2f}")
        st.write(f"RSI: {result['rsi']:.1f}")
        st.write(f"Bullish Score: {result['score']}/6")
        st.write(f"Estimated Odds Up: {result['odds']}%")

        st.line_chart(result["chart"])

# ---------- TOP 10 STOCK SCANNER ----------

st.header("Top 10 Stocks This Week")

tickers = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "GOOGL", "TSLA", "AMD", "NFLX", "PLTR",
    "JPM", "V", "MA", "COST", "AVGO",
    "SPY", "QQQ", "DIA", "IWM"
]

results = []

with st.spinner("Scanning stocks..."):
    for stock in tickers:
        result = calculate_score(stock)

        if result:
            results.append({
                "Ticker": result["ticker"],
                "Score": result["score"],
                "RSI": round(result["rsi"], 1),
                "Odds Up %": result["odds"]
            })

if results:
    df = pd.DataFrame(results)

    df = df.sort_values(
        by=["Score", "Odds Up %"],
        ascending=False
    )

    st.dataframe(df.head(10), use_container_width=True)
