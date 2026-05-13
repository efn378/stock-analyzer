import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Stock Odds Analyzer",
    layout="wide"
)

st.title("📈 Stock Odds Analyzer")


# ---------- CALCULATION ENGINE ----------

def calculate_score(ticker):

    try:

        data = yf.download(
            ticker,
            period="20y",
            auto_adjust=True,
            progress=False
        )

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

        one_week = (
            (latest_close / float(close.iloc[-5])) - 1
        ) * 100

        one_month = (
            (latest_close / float(close.iloc[-21])) - 1
        ) * 100

        three_month = (
            (latest_close / float(close.iloc[-63])) - 1
        ) * 100

        volatility = float(
            close.pct_change().tail(63).std()
            * np.sqrt(252)
            * 100
        )

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

        trend_score += min(
            max((latest_close / latest_sma200 - 1) * 100, 0),
            25
        )

        trend_score += min(
            max((latest_close / latest_sma50 - 1) * 100, 0),
            15
        )

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

        rank_score = (
            trend_score
            + momentum_score
            + rsi_score
            - volatility_penalty
        )

        rank_score = round(
            max(min(rank_score, 100), 0),
            1
        )

        if (
            latest_close > latest_sma200
            and latest_sma50 > latest_sma200
        ):
            trend = "Bullish"

        elif latest_close < latest_sma200:
            trend = "Bearish"

        else:
            trend = "Neutral"

        # ---------- PREDICTIONS ----------

        expected_week_move = (
            (rank_score / 100) * 4
            - (volatility / 100)
        )

        expected_month_move = (
            (rank_score / 100) * 10
            - (volatility / 50)
        )

        predicted_week_price = latest_close * (
            1 + expected_week_move / 100
        )

        predicted_month_price = latest_close * (
            1 + expected_month_move / 100
        )

        if rank_score >= 85:
            confidence = "High"

        elif rank_score >= 70:
            confidence = "Moderate"

        else:
            confidence = "Low"

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
            "predicted_week_price": predicted_week_price,
            "predicted_month_price": predicted_month_price,
            "confidence": confidence,
            "chart": close
        }

    except Exception:
        return None


# ---------- SINGLE STOCK ANALYZER ----------

st.header("🔍 Single Stock Analysis")

ticker = st.text_input(
    "Enter ticker",
    "AAPL"
).upper()

if ticker:

    result = calculate_score(ticker)

    if result:

        st.subheader(f"📊 {result['ticker']}")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Current Price",
            f"${result['price']:.2f}"
        )

        col2.metric(
            "1 Week Target",
            f"${result['predicted_week_price']:.2f}",
            f"{((result['predicted_week_price'] / result['price']) - 1) * 100:.1f}%"
        )

        col3.metric(
            "1 Month Target",
            f"${result['predicted_month_price']:.2f}",
            f"{((result['predicted_month_price'] / result['price']) - 1) * 100:.1f}%"
        )

        st.divider()

        col4, col5, col6 = st.columns(3)

        col4.metric(
            "Ranking Score",
            f"{result['rank_score']}/100"
        )

        col5.metric(
            "RSI",
            f"{result['rsi']:.1f}"
        )

        col6.metric(
            "Volatility",
            f"{result['volatility']:.1f}%"
        )

        st.progress(result["rank_score"] / 100)

        st.write(f"### Trend: {result['trend']}")
        st.write(f"### Confidence: {result['confidence']}")
        st.write(f"### Bullish Score: {result['bullish_score']}/6")

        st.divider()

        chart_data = pd.DataFrame({
            "Metric": [
                "Ranking Score",
                "RSI",
                "Bullish %",
                "Confidence"
            ],
            "Value": [
                result["rank_score"],
                result["rsi"],
                (result["bullish_score"] / 6) * 100,
                100 if result["confidence"] == "High"
                else 70 if result["confidence"] == "Moderate"
                else 40
            ]
        })

        st.write("## 📊 Technical Strength")

        st.bar_chart(
            chart_data,
            x="Metric",
            y="Value"
        )

        st.divider()

        prediction_data = pd.DataFrame({
            "Time": [
                "Current",
                "1 Week",
                "1 Month"
            ],
            "Price": [
                result["price"],
                result["predicted_week_price"],
                result["predicted_month_price"]
            ]
        })

        st.write("## 🔮 Predicted Price Path")

        st.line_chart(
            prediction_data,
            x="Time",
            y="Price"
        )

        st.divider()

        st.write("## 📈 20 Year Price History")

        st.line_chart(result["chart"])

    else:
        st.error("No data found.")


# ---------- STOCK UNIVERSE ----------

tickers = [

    # Mega-cap / growth
    "AAPL", "MSFT", "NVDA", "AMZN", "META",
    "GOOGL", "GOOG", "TSLA", "AVGO", "AMD",
    "NFLX", "PLTR", "ADBE", "CRM", "ORCL",
    "INTC", "QCOM", "TXN", "MU", "NOW",
    "SHOP", "UBER", "ABNB", "SNOW", "PANW",
    "CRWD", "ZS", "NET", "DDOG", "MDB",
    "COIN", "RBLX",

    # Large caps
    "COST", "WMT", "HD", "LOW", "MCD",
    "SBUX", "NKE", "DIS", "V", "MA",
    "AXP", "JPM", "BAC", "GS", "MS",
    "BLK", "UNH", "LLY", "JNJ", "ABBV",
    "MRK", "PFE", "TMO", "ISRG", "CAT",
    "DE", "GE", "HON", "RTX", "LMT",
    "BA", "UPS",

    # Energy
    "XOM", "CVX", "COP", "SLB",
    "OXY", "EOG", "NEM", "GOLD",

    # ETFs
    "SPY", "QQQ", "DIA", "IWM",
    "VTI", "VOO", "SCHD", "XLK",
    "XLF", "XLE", "XLV", "SMH",
    "SOXX", "ARKK",

    # Canadian
    "SHOP.TO", "RY.TO", "TD.TO",
    "BNS.TO", "BMO.TO", "CM.TO",
    "NA.TO", "ENB.TO", "TRP.TO",
    "CNQ.TO", "SU.TO", "CVE.TO",
    "CP.TO", "CNR.TO", "BAM.TO",
    "BN.TO", "ATD.TO", "CSU.TO",
    "WCN.TO", "FTS.TO", "EMA.TO",
    "AQN.TO", "T.TO", "BCE.TO",
    "NTR.TO", "TECK-B.TO",
    "ABX.TO", "WPM.TO",

    # Canadian ETFs
    "XEQT.TO", "VEQT.TO",
    "VFV.TO", "XQQ.TO",
    "ZSP.TO", "ZWB.TO",
    "BK.TO", "XIU.TO",
    "XIC.TO"
]


# ---------- TOP STOCKS ----------

st.header("🏆 Top Stocks This Week")

results = []

with st.spinner("Scanning stocks..."):

    for stock in tickers:

        result = calculate_score(stock)

        if result:

            results.append({

                "Ticker":
                result["ticker"],

                "Current":
                round(result["price"], 2),

                "1W Target":
                round(
                    result["predicted_week_price"],
                    2
                ),

                "1M Target":
                round(
                    result["predicted_month_price"],
                    2
                ),

                "Confidence":
                result["confidence"],

                "Rank":
                result["rank_score"],

                "Trend":
                result["trend"],

                "RSI":
                round(
                    result["rsi"],
                    1
                )
            })

if results:

    df = pd.DataFrame(results)

    df = df.sort_values(
        by="Rank",
        ascending=False
    )

    df = df.reset_index(drop=True)

    df.index = df.index + 1

    st.dataframe(
        df.head(25),
        use_container_width=True
    )
