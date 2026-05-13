import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np

st.title("Stock Odds Analyzer")

def calculate_score(ticker):
    try:
        data = yf.download(ticker, period="20y", auto_adjust=True, progress=False)

        if data.empty or len(data) < 220:
            return None

        close = data["Close"]

        if hasattr(close, "columns"):
            close = close.iloc[:, 0]

        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()

        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        latest_close = float(close.iloc[-1])
        latest_sma50 = float(sma50.iloc[-1])
        latest_sma200 = float(sma200.iloc[-1])
        latest_rsi = float(rsi.iloc[-1])

        one_week = ((latest_close / float(close.iloc[-5])) - 1) * 100
        one_month = ((latest_close / float(close.iloc[-21])) - 1) * 100
        three_month = ((latest_close / float(close.iloc[-63])) - 1) * 100

        volatility = float(close.pct_change().tail(63).std() * np.sqrt(252) * 100)

        bullish_score = 0

        if latest_close > latest_sma200:
            bullish_score += 2
        if latest_sma50 > latest_sma200:
            bullish_score += 2
        if 40 <= latest_rsi <= 70:
            bullish_score += 1
        if latest_close > latest_sma50:
            bullish_score += 1

        trend_score = 0
        trend_score += min(max((latest_close / latest_sma200 - 1) * 100, 0), 25)
        trend_score += min(max((latest_close / latest_sma50 - 1) * 100, 0), 15)

        momentum_score = 0
        momentum_score += min(max(one_week, -5), 10) + 5
        momentum_score += min(max(one_month, -10), 15) + 10
        momentum_score += min(max(three_month, -20), 25) + 20

        if 45 <= latest_rsi <= 65:
            rsi_score = 20
        elif 35 <= latest_rsi < 45 or 65 < latest_rsi <= 75:
            rsi_score = 12
        else:
            rsi_score = 4

        volatility_penalty = min(volatility / 4, 15)

        rank_score = trend_score + momentum_score + rsi_score - volatility_penalty
        rank_score = round(max(min(rank_score, 100), 0), 1)

        if latest_close > latest_sma200 and latest_sma50 > latest_sma200:
            trend = "Bullish"
        elif latest_close < latest_sma200:
            trend = "Bearish"
        else:
            trend = "Neutral"

        return {
            "ticker": ticker,
            "price": latest_close,
            "rsi": latest_rsi,
            "bullish_score": bullish_score,
            "rank_score": rank_score,
            "one_week": one_week,
            "one_month": one_month,
            "three_month": three_month,
            "volatility": volatility,
            "trend": trend,
            "chart": close
        }

    except Exception:
        return None


# ---------- SINGLE STOCK ANALYZER ----------

st.header("Single Stock Analysis")

ticker = st.text_input("Enter ticker", "AAPL").upper()

if ticker:
    result = calculate_score(ticker)

    if result:
        st.subheader(result["ticker"])
        st.write(f"Current Price: ${result['price']:.2f}")
        st.write(f"RSI: {result['rsi']:.1f}")
        st.write(f"Bullish Score: {result['bullish_score']}/6")
        st.write(f"Ranking Score: {result['rank_score']}/100")
        st.write(f"Trend: {result['trend']}")
        st.write(f"1 Week Return: {result['one_week']:.1f}%")
        st.write(f"1 Month Return: {result['one_month']:.1f}%")
        st.write(f"3 Month Return: {result['three_month']:.1f}%")
        st.write(f"Volatility: {result['volatility']:.1f}%")

        st.line_chart(result["chart"])
    else:
        st.error("No data found.")


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
                "Rank Score": result["rank_score"],
                "Bullish": f"{result['bullish_score']}/6",
                "Trend": result["trend"],
                "RSI": round(result["rsi"], 1),
                "1W %": round(result["one_week"], 1),
                "1M %": round(result["one_month"], 1),
                "3M %": round(result["three_month"], 1),
                "Volatility %": round(result["volatility"], 1)
            })

if results:
    df = pd.DataFrame(results)
    df = df.sort_values(by="Rank Score", ascending=False)
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    st.dataframe(df.head(10), use_container_width=True)
