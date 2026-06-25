import streamlit as st
import yfinance as yf
import pandas as pd
import time
import pytz
from datetime import datetime

chicago = pytz.timezone("America/Chicago")
now = datetime.now(chicago)

st.set_page_config(
    page_title="Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    h1 { color: #00d4aa !important; }
    h2, h3 { color: #ffffff !important; }
    .stDataFrame { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📈 Live Stock Comparison Dashboard")
col_date, col_refresh = st.columns([3,1])
with col_date:
    st.write("🕐 Updated: " + now.strftime("%B %d, %Y %I:%M %p") + " CST")
with col_refresh:
    st.write("Data cached for 1 hour")
st.divider()

companies = {
    "Nike": "NKE",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "JPMorgan": "JPM",
    "Morningstar": "MORN",
    "CME Group": "CME",
    "Northern Trust": "NTRS",
    "Goldman Sachs": "GS",
    "Amazon": "AMZN",
    "Tesla": "TSLA"
}

@st.cache_data(ttl=3600)
def get_stock_data():
    data = []
    for name, ticker in companies.items():
        try:
            info = yf.Ticker(ticker).info
            price  = info.get("currentPrice", 0)
            prev   = info.get("previousClose", price)
            change = round(price - prev, 2)
            pct    = round((change / prev) * 100, 2) if prev else 0
            data.append({
                "Company":         name,
                "Price ($)":       price,
                "Change (%)":      pct,
                "Market Cap $B":   round(info.get("marketCap", 0) / 1e9, 2),
                "Revenue $B":      round(info.get("totalRevenue", 0) / 1e9, 2),
                "PE Ratio":        round(info.get("trailingPE", 0), 2),
                "PB Ratio":        round(info.get("priceToBook", 0), 2),
                "EPS ($)":         round(info.get("trailingEps", 0), 2),
                "ROE (%)":         round(info.get("returnOnEquity", 0) * 100, 2),
                "ROA (%)":         round(info.get("returnOnAssets", 0) * 100, 2),
                "Profit Margin %": round(info.get("profitMargins", 0) * 100, 2),
                "Debt/Equity":     round(info.get("debtToEquity", 0), 2),
                "Current Ratio":   round(info.get("currentRatio", 0), 2),
                "Div Yield (%)":   round(info.get("dividendYield", 0) * 100, 2),
                "52W High ($)":    info.get("fiftyTwoWeekHigh", 0),
                "52W Low ($)":     info.get("fiftyTwoWeekLow", 0),
            })
            time.sleep(0.5)
        except:
            pass
    return pd.DataFrame(data)

with st.spinner("Loading live market data..."):
    df = get_stock_data()

# KPI Metrics Row
st.subheader("📊 Market Snapshot")
cols = st.columns(5)
top5 = df.nlargest(5, "Market Cap $B")
for i, (_, row) in enumerate(top5.iterrows()):
    with cols[i]:
        arrow = "🟢" if row["Change (%)"] > 0 else "🔴"
        st.metric(
            label=row["Company"],
            value=f"${row['Price ($)']}",
            delta=f"{row['Change (%)']}%"
        )
st.divider()

# Tabs for clean navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "💰 Live Prices",
    "📐 Valuation Ratios",
    "💹 Profitability",
    "📈 Charts"
])

with tab1:
    st.subheader("Live Stock Prices")
    def color(val):
        if isinstance(val, (int, float)):
            c = "green" if val > 0 else "red"
            return f"color: {c}; font-weight: bold"
        return ""
    price_df = df[["Company","Price ($)","Change (%)","Market Cap $B","52W High ($)","52W Low ($)"]]
    st.dataframe(
        price_df.style.map(color, subset=["Change (%)"]),
        use_container_width=True,
        height=400
    )

with tab2:
    st.subheader("Valuation Ratios")
    val_df = df[["Company","PE Ratio","PB Ratio","EPS ($)","Div Yield (%)"]]
    st.dataframe(val_df, use_container_width=True, height=400)
    st.caption("PE = Price/Earnings | PB = Price/Book | EPS = Earnings Per Share")

with tab3:
    st.subheader("Profitability & Financial Health")
    prof_df = df[["Company","Revenue $B","Profit Margin %","ROE (%)","ROA (%)","Debt/Equity","Current Ratio"]]
    st.dataframe(prof_df, use_container_width=True, height=400)
    st.caption("ROE = Return on Equity | ROA = Return on Assets")

with tab4:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("PE Ratio Comparison")
        st.bar_chart(df.set_index("Company")["PE Ratio"])
    with col2:
        st.subheader("Profit Margin %")
        st.bar_chart(df.set_index("Company")["Profit Margin %"])

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Revenue $B")
        st.bar_chart(df.set_index("Company")["Revenue $B"])
    with col4:
        st.subheader("Market Cap $B")
        st.bar_chart(df.set_index("Company")["Market Cap $B"])

st.divider()

# Stock History
st.subheader("📉 Stock Price History")
col_sel, col_per = st.columns([2,3])
with col_sel:
    selected = st.selectbox("Select Company", list(companies.keys()))
with col_per:
    period = st.radio("Period", ["1mo","3mo","6mo","1y","2y","5y"], horizontal=True)

history = yf.Ticker(companies[selected]).history(period=period)
st.line_chart(history["Close"])
st.divider()

# Compare Two
st.subheader("⚖️ Compare Two Companies")
col5, col6 = st.columns(2)
with col5:
    comp1 = st.selectbox("Company 1", list(companies.keys()), index=0)
with col6:
    comp2 = st.selectbox("Company 2", list(companies.keys()), index=1)

h1 = yf.Ticker(companies[comp1]).history(period="1y")["Close"]
h2 = yf.Ticker(companies[comp2]).history(period="1y")["Close"]
compare_df = pd.DataFrame({comp1: h1, comp2: h2})
st.line_chart(compare_df)

st.divider()
st.caption("Built by Poonam Dhanuka | DePaul MS Finance | Data: Yahoo Finance")
