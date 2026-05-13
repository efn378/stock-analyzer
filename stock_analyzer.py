import yfinance as yf
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Stock & ETF Analyzer", layout="wide")

st.title("📈 Ultimate Stock & ETF Analyzer")
st.caption("Educational tool only. Forecasts are estimates, not guarantees.")

# ---------- SETTINGS ----------

tickers = [
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA",
    "AVGO", "AMD", "NFLX", "PLTR", "ADBE", "CRM", "ORCL", "INTC",
    "QCOM", "MU", "NOW", "SHOP", "UBER", "ABNB", "SNOW", "PANW",
    "CRWD", "NET", "COIN", "RBLX",

    "COST", "WMT", "HD", "LOW", "MCD", "SBUX", "DIS", "V", "MA",
    "AXP", "JPM", "BAC", "GS", "MS", "BLK", "UNH", "LLY", "JNJ",
    "ABBV", "MRK", "PFE", "TMO", "ISRG", "CAT", "DE", "GE", "HON",
    "RTX", "LMT", "BA", "UPS",

    "XOM", "CVX", "COP", "SLB", "OXY", "EOG", "NEM", "GOLD",

    "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "SCHD", "XLK",
    "XLF", "XLE", "XLV", "SMH", "SOXX", "ARKK",

    "SHOP.TO", "RY.TO", "TD.TO", "BNS.TO", "BMO.TO", "CM.TO",
    "NA.TO", "ENB.TO", "TRP.TO", "CNQ.TO", "SU.TO", "CVE.TO",
    "CP.TO", "CNR.TO", "BAM.TO", "BN.TO", "ATD.TO", "CSU.TO",
    "WCN.TO", "FTS.TO", "EMA.TO", "AQN.TO", "T.TO", "BCE.TO",
    "NTR.TO", "TECK-B.TO", "ABX.TO", "WPM.TO",

    "XEQT.TO", "VEQT.TO", "VFV.TO", "XQQ.TO", "ZSP.TO",
    "ZWB.TO", "BK.TO", "XIU.TO", "XIC.TO"
]

sector_etfs = {
    "Technology": "XLK",
    "Semiconductors": "SMH",
    "Financials": "XLF",
    "Energy": "XLE",
    "Healthcare": "XLV",
    "Market": "SPY",
    "Nasdaq": "QQQ"
}

# ---------- DATA FUNCTIONS ----------

@st.cache_data(ttl=3600)
def get_price_data(ticker):
    return yf.download(ticker, period="20y", auto_adjust=True, progress=False)

@st.cache_data(ttl=3600)
def get_info(ticker):
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}

def safe_float(value, default=0):
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default

def calculate_rsi(close, window=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def backtest_setup(close, sma50, sma200, rsi):
    rows = []

    for i in range(220, len(close) - 21):
        setup = (
            close.iloc[i] > sma200.iloc[i]
            and sma50.iloc[i] > sma200.iloc[i]
            and 35 <= rsi.iloc[i] <= 75
        )

        if setup:
            future_1w = ((close.iloc[i + 5] / close.iloc[i]) - 1) * 100
            future_1m = ((close.iloc[i + 21] / close.iloc[i]) - 1) * 100
            rows.append([future_1w, future_1m])

    if len(rows) < 10:
        return {
            "samples": len(rows),
            "win_1w": 50,
            "win_1m": 50,
            "avg_1w": 0,
            "avg_1m": 0
        }

    df = pd.DataFrame(rows, columns=["1W", "1M"])

    return {
        "samples": len(df),
        "win_1w": round((df["1W"] > 0).mean() * 100, 1),
        "win_1m": round((df["1M"] > 0).mean() * 100, 1),
        "avg_1w": round(df["1W"].mean(), 2),
        "avg_1m": round(df["1M"].mean(), 2)
    }

def analyze_stock(ticker):
    try:
        data = get_price_data(ticker)

        if data.empty or len(data) < 220:
            return None

        close = data["Close"]

        if hasattr(close, "columns"):
            close = close.iloc[:, 0]

        high = data["High"]
        low = data["Low"]
        volume = data["Volume"]

        if hasattr(high, "columns"):
            high = high.iloc[:, 0]
        if hasattr(low, "columns"):
            low = low.iloc[:, 0]
        if hasattr(volume, "columns"):
            volume = volume.iloc[:, 0]

        sma20 = close.rolling(20).mean()
        sma50 = close.rolling(50).mean()
        sma200 = close.rolling(200).mean()
        rsi = calculate_rsi(close)

        latest = float(close.iloc[-1])
        s20 = float(sma20.iloc[-1])
        s50 = float(sma50.iloc[-1])
        s200 = float(sma200.iloc[-1])
        latest_rsi = float(rsi.iloc[-1])

        one_week = ((latest / float(close.iloc[-5])) - 1) * 100
        one_month = ((latest / float(close.iloc[-21])) - 1) * 100
        three_month = ((latest / float(close.iloc[-63])) - 1) * 100
        six_month = ((latest / float(close.iloc[-126])) - 1) * 100
        one_year = ((latest / float(close.iloc[-252])) - 1) * 100

        volatility = float(close.pct_change().tail(63).std() * np.sqrt(252) * 100)

        avg_volume = float(volume.tail(30).mean())
        volume_ratio = float(volume.iloc[-1] / avg_volume) if avg_volume > 0 else 1

        support = float(low.tail(90).min())
        resistance = float(high.tail(90).max())

        drawdown = ((latest / float(close.tail(252).max())) - 1) * 100

        info = get_info(ticker)

        pe = safe_float(info.get("trailingPE"), None)
        forward_pe = safe_float(info.get("forwardPE"), None)
        peg = safe_float(info.get("pegRatio"), None)
        market_cap = safe_float(info.get("marketCap"), None)
        dividend_yield = safe_float(info.get("dividendYield"), 0) * 100
        beta = safe_float(info.get("beta"), None)
        profit_margin = safe_float(info.get("profitMargins"), None)
        revenue_growth = safe_float(info.get("revenueGrowth"), None)
        earnings_growth = safe_float(info.get("earningsGrowth"), None)

        bullish_score = 0
        if latest > s200:
            bullish_score += 2
        if s50 > s200:
            bullish_score += 2
        if 40 <= latest_rsi <= 70:
            bullish_score += 1
        if latest > s50:
            bullish_score += 1

        trend_score = 0
        trend_score += min(max((latest / s200 - 1) * 100, 0), 25)
        trend_score += min(max((latest / s50 - 1) * 100, 0), 15)

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

        valuation_score = 10
        if pe and pe > 0:
            if pe < 20:
                valuation_score += 8
            elif pe < 35:
                valuation_score += 4
            elif pe > 60:
                valuation_score -= 5

        if peg and peg > 0:
            if peg < 1.5:
                valuation_score += 5
            elif peg > 3:
                valuation_score -= 3

        growth_score = 0
        if revenue_growth:
            growth_score += min(max(revenue_growth * 100, -10), 25)
        if earnings_growth:
            growth_score += min(max(earnings_growth * 100, -10), 25)

        dividend_score = min(dividend_yield * 3, 10)

        volatility_penalty = min(volatility / 4, 18)
        overextended_penalty = 0

        if latest_rsi > 78:
            overextended_penalty += 8
        if one_month > 25:
            overextended_penalty += 8
        if latest > s50 * 1.18:
            overextended_penalty += 6

        backtest = backtest_setup(close, sma50, sma200, rsi)

        historical_score = ((backtest["win_1m"] - 50) * 0.7) + (backtest["avg_1m"] * 2)

        rank_score = (
            trend_score
            + momentum_score
            + rsi_score
            + valuation_score
            + growth_score
            + dividend_score
            + historical_score
            - volatility_penalty
            - overextended_penalty
        )

        rank_score = round(max(min(rank_score, 100), 0), 1)

        if latest > s200 and s50 > s200:
            trend = "Bullish"
        elif latest < s200:
            trend = "Bearish"
        else:
            trend = "Neutral"

        expected_week_move = (
            backtest["avg_1w"] * 0.5
            + one_week * 0.15
            + (rank_score / 100) * 2
            - volatility / 120
        )

        expected_month_move = (
            backtest["avg_1m"] * 0.5
            + one_month * 0.15
            + (rank_score / 100) * 5
            - volatility / 60
        )

        predicted_week = latest * (1 + expected_week_move / 100)
        predicted_month = latest * (1 + expected_month_move / 100)

        downside_1m = latest * (1 - (volatility / 100) / np.sqrt(12))
        upside_1m = latest * (1 + (volatility / 100) / np.sqrt(12))

        if rank_score >= 82 and backtest["win_1m"] >= 58:
            rating = "Strong Buy"
            confidence = "High"
        elif rank_score >= 68:
            rating = "Buy / Watch"
            confidence = "Moderate"
        elif rank_score >= 50:
            rating = "Neutral"
            confidence = "Low"
        else:
            rating = "Avoid / Weak"
            confidence = "Low"

        reasons = []

        if trend == "Bullish":
            reasons.append("Price is in a bullish trend above major moving averages.")
        elif trend == "Bearish":
            reasons.append("Price is below the 200-day average, which weakens the setup.")

        if latest_rsi > 75:
            reasons.append("RSI is high, so the stock may be short-term overextended.")
        elif latest_rsi < 35:
            reasons.append("RSI is low, which can mean oversold but still risky.")
        else:
            reasons.append("RSI is in a healthier momentum range.")

        if one_month > 0 and three_month > 0:
            reasons.append("Recent 1-month and 3-month momentum are positive.")

        if volatility > 55:
            reasons.append("Volatility is high, so price targets are less reliable.")

        if backtest["samples"] >= 10:
            reasons.append(
                f"Similar historical setups were positive 1 month later "
                f"{backtest['win_1m']}% of the time."
            )

        return {
            "ticker": ticker,
            "price": latest,
            "sma20": s20,
            "sma50": s50,
            "sma200": s200,
            "rsi": latest_rsi,
            "one_week": one_week,
            "one_month": one_month,
            "three_month": three_month,
            "six_month": six_month,
            "one_year": one_year,
            "volatility": volatility,
            "volume_ratio": volume_ratio,
            "support": support,
            "resistance": resistance,
            "drawdown": drawdown,
            "pe": pe,
            "forward_pe": forward_pe,
            "peg": peg,
            "market_cap": market_cap,
            "dividend_yield": dividend_yield,
            "beta": beta,
            "profit_margin": profit_margin,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "bullish_score": bullish_score,
            "rank_score": rank_score,
            "trend": trend,
            "rating": rating,
            "confidence": confidence,
            "predicted_week": predicted_week,
            "predicted_month": predicted_month,
            "expected_week_move": expected_week_move,
            "expected_month_move": expected_month_move,
            "downside_1m": downside_1m,
            "upside_1m": upside_1m,
            "backtest": backtest,
            "reasons": reasons,
            "close": close,
            "data": data
        }

    except Exception:
        return None

# ---------- UI HELPERS ----------

def money(value):
    if value is None:
        return "N/A"
    if value >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,.0f}"

def pct(value):
    if value is None:
        return "N/A"
    return f"{value:.1f}%"

def make_gauge(title, value):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "royalblue"},
            "steps": [
                {"range": [0, 50], "color": "#ffcccc"},
                {"range": [50, 75], "color": "#fff2cc"},
                {"range": [75, 100], "color": "#d9ead3"}
            ]
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def make_price_chart(result):
    close = result["close"]
    df = pd.DataFrame({
        "Close": close,
        "SMA50": close.rolling(50).mean(),
        "SMA200": close.rolling(200).mean()
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["Close"], name="Price"))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="50 DMA"))
    fig.add_trace(go.Scatter(x=df.index, y=df["SMA200"], name="200 DMA"))
    fig.update_layout(height=450, title="Price Trend", margin=dict(l=20, r=20, t=50, b=20))
    return fig

def make_prediction_chart(result):
    df = pd.DataFrame({
        "Time": ["Current", "1 Week Target", "1 Month Target"],
        "Price": [
            result["price"],
            result["predicted_week"],
            result["predicted_month"]
        ]
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Time"],
        y=df["Price"],
        mode="lines+markers",
        name="Forecast"
    ))
    fig.update_layout(height=330, title="Forecast Path", margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ---------- APP ----------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Single Analyzer",
    "🏆 Scanner",
    "🔥 Sector Strength",
    "💰 Dividend / ETF View",
    "ℹ️ How To Read It"
])

# ---------- SINGLE ANALYZER ----------

with tab1:
    ticker = st.text_input("Enter ticker", "AAPL").upper().strip()

    result = analyze_stock(ticker)

    if result:
        st.subheader(f"{result['ticker']} — {result['rating']}")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Current Price", f"${result['price']:.2f}")
        c2.metric("1W Target", f"${result['predicted_week']:.2f}", pct(result["expected_week_move"]))
        c3.metric("1M Target", f"${result['predicted_month']:.2f}", pct(result["expected_month_move"]))
        c4.metric("Rating", result["rating"])

        c5, c6, c7, c8 = st.columns(4)

        c5.metric("Rank Score", f"{result['rank_score']}/100")
        c6.metric("RSI", f"{result['rsi']:.1f}")
        c7.metric("Trend", result["trend"])
        c8.metric("Confidence", result["confidence"])

        g1, g2, g3 = st.columns(3)

        with g1:
            st.plotly_chart(make_gauge("Overall Score", result["rank_score"]), use_container_width=True)

        with g2:
            st.plotly_chart(make_gauge("1M Historical Win Rate", result["backtest"]["win_1m"]), use_container_width=True)

        with g3:
            strength = max(min((result["bullish_score"] / 6) * 100, 100), 0)
            st.plotly_chart(make_gauge("Technical Strength", strength), use_container_width=True)

        st.divider()

        left, right = st.columns([2, 1])

        with left:
            st.plotly_chart(make_price_chart(result), use_container_width=True)

        with right:
            st.plotly_chart(make_prediction_chart(result), use_container_width=True)

            st.write("### 1 Month Range Estimate")
            st.write(f"Downside: **${result['downside_1m']:.2f}**")
            st.write(f"Base Target: **${result['predicted_month']:.2f}**")
            st.write(f"Upside: **${result['upside_1m']:.2f}**")

        st.divider()

        st.write("## AI-Style Summary")
        for reason in result["reasons"]:
            st.write(f"✅ {reason}")

        st.divider()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("1W Return", pct(result["one_week"]))
        m2.metric("1M Return", pct(result["one_month"]))
        m3.metric("3M Return", pct(result["three_month"]))
        m4.metric("1Y Return", pct(result["one_year"]))

        f1, f2, f3, f4 = st.columns(4)
        f1.metric("P/E", "N/A" if result["pe"] is None else f"{result['pe']:.1f}")
        f2.metric("Forward P/E", "N/A" if result["forward_pe"] is None else f"{result['forward_pe']:.1f}")
        f3.metric("Dividend Yield", pct(result["dividend_yield"]))
        f4.metric("Market Cap", money(result["market_cap"]))

        f5, f6, f7, f8 = st.columns(4)
        f5.metric("Revenue Growth", "N/A" if result["revenue_growth"] is None else pct(result["revenue_growth"] * 100))
        f6.metric("Earnings Growth", "N/A" if result["earnings_growth"] is None else pct(result["earnings_growth"] * 100))
        f7.metric("Volatility", pct(result["volatility"]))
        f8.metric("Volume vs Avg", f"{result['volume_ratio']:.2f}x")

        st.write("## Historical Backtest")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Setup Samples", result["backtest"]["samples"])
        b2.metric("1W Win Rate", pct(result["backtest"]["win_1w"]))
        b3.metric("1M Win Rate", pct(result["backtest"]["win_1m"]))
        b4.metric("Avg 1M Move", pct(result["backtest"]["avg_1m"]))

    else:
        st.error("No data found for that ticker.")

# ---------- SCANNER ----------

with tab2:
    st.subheader("Top Ranked Stocks & ETFs")

    results = []

    with st.spinner("Scanning stock universe..."):
        for stock in tickers:
            r = analyze_stock(stock)
            if r:
                results.append({
                    "Ticker": r["ticker"],
                    "Rating": r["rating"],
                    "Current": round(r["price"], 2),
                    "1W Target": round(r["predicted_week"], 2),
                    "1M Target": round(r["predicted_month"], 2),
                    "1M Range Low": round(r["downside_1m"], 2),
                    "1M Range High": round(r["upside_1m"], 2),
                    "Rank": r["rank_score"],
                    "1M Win %": r["backtest"]["win_1m"],
                    "Trend": r["trend"],
                    "RSI": round(r["rsi"], 1),
                    "1M %": round(r["one_month"], 1),
                    "3M %": round(r["three_month"], 1),
                    "Volatility %": round(r["volatility"], 1),
                    "Dividend %": round(r["dividend_yield"], 2)
                })

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by=["Rank", "1M Win %"], ascending=False)
        df = df.reset_index(drop=True)
        df.index = df.index + 1

        st.dataframe(df.head(30), use_container_width=True)

# ---------- SECTOR STRENGTH ----------

with tab3:
    st.subheader("Sector Strength")

    sector_results = []

    for name, symbol in sector_etfs.items():
        r = analyze_stock(symbol)
        if r:
            sector_results.append({
                "Sector": name,
                "ETF": symbol,
                "Rank": r["rank_score"],
                "Trend": r["trend"],
                "1M %": round(r["one_month"], 1),
                "3M %": round(r["three_month"], 1),
                "RSI": round(r["rsi"], 1)
            })

    if sector_results:
        sector_df = pd.DataFrame(sector_results).sort_values(by="Rank", ascending=False)
        st.dataframe(sector_df, use_container_width=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(x=sector_df["Sector"], y=sector_df["Rank"]))
        fig.update_layout(height=400, title="Sector Rank Scores")
        st.plotly_chart(fig, use_container_width=True)

# ---------- DIVIDEND / ETF VIEW ----------

with tab4:
    st.subheader("Dividend & ETF Friendly View")

    dividend_rows = []

    for stock in tickers:
        r = analyze_stock(stock)
        if r and r["dividend_yield"] > 1:
            dividend_rows.append({
                "Ticker": r["ticker"],
                "Dividend %": round(r["dividend_yield"], 2),
                "Rank": r["rank_score"],
                "Rating": r["rating"],
                "Trend": r["trend"],
                "Volatility %": round(r["volatility"], 1),
                "1M Target": round(r["predicted_month"], 2)
            })

    if dividend_rows:
        div_df = pd.DataFrame(dividend_rows).sort_values(
            by=["Rank", "Dividend %"],
            ascending=False
        )
        div_df = div_df.reset_index(drop=True)
        div_df.index = div_df.index + 1
        st.dataframe(div_df.head(30), use_container_width=True)

# ---------- HELP ----------

with tab5:
    st.write("""
## What this app does

This app combines:

- 20 years of price history
- Moving averages
- RSI
- Momentum
- Volatility
- Historical backtesting
- Basic valuation
- Dividend yield
- Growth metrics
- Sector strength
- Support and resistance
- Forecast ranges

## Best number to watch

**Rank Score** is the main overall score.

- 80+ = strong setup
- 65–80 = decent setup
- 50–65 = neutral
- Below 50 = weak

## Most reliable section

The **Historical Backtest** section is the most useful because it checks how similar setups performed in the past.

## Important

The 1-week and 1-month targets are estimates. They are not guarantees.
Use them as probability-based guidance, not certainty.
""")
