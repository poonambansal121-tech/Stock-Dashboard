import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("Live Stock Comparison Dashboard")
st.write("Updated: " + datetime.now().strftime("%B %d, %Y %I:%M %p"))
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

data = []
for name, ticker in companies.items():
    info = yf.Ticker(ticker).info
    price   = info.get("currentPrice", 0)
    prev    = info.get("previousClose", price)
    change  = round(price - prev, 2)
    pct     = round((change / prev) * 100, 2) if prev else 0
    data.append({
        "Company":        name,
        "Price ($)":      price,
        "Change (%)":     pct,
        "Market Cap $B":  round(info.get("marketCap", 0) / 1e9, 2),
        "Revenue $B":     round(info.get("totalRevenue", 0) / 1e9, 2),
        "PE Ratio":       round(info.get("trailingPE", 0), 2),
        "PB Ratio":       round(info.get("priceToBook", 0), 2),
        "EPS ($)":        round(info.get("trailingEps", 0), 2),
        "ROE (%)":        round(info.get("returnOnEquity", 0) * 100, 2),
        "ROA (%)":        round(info.get("returnOnAssets", 0) * 100, 2),
        "Profit Margin %":round(info.get("profitMargins", 0) * 100, 2),
        "Debt/Equity":    round(info.get("debtToEquity", 0), 2),
        "Current Ratio":  round(info.get("currentRatio", 0), 2),
        "Div Yield (%)":  round(info.get("dividendYield", 0) * 100, 2),
        "52W High ($)":   info.get("fiftyTwoWeekHigh", 0),
        "52W Low ($)":    info.get("fiftyTwoWeekLow", 0),
    })

df = pd.DataFrame(data)

def color(val):
    if isinstance(val, (int, float)):
        c = "green" if val > 0 else "red"
        return f"color: {c}"
    return ""

st.subheader("Live Prices & Market Cap")
price_df = df[["Company","Price ($)","Change (%)","Market Cap $B","52W High ($)","52W Low ($)"]]
st.dataframe(
    price_df.style.map(color, subset=["Change (%)"]),
    use_container_width=True
)
st.divider()

st.subheader("Valuation Ratios")
val_df = df[["Company","PE Ratio","PB Ratio","EPS ($)","Div Yield (%)"]]
st.dataframe(val_df, use_container_width=True)
st.caption("PE = Price/Earnings | PB = Price/Book | EPS = Earnings Per Share")
st.divider()

st.subheader("Profitability & Financial Health")
prof_df = df[["Company","Revenue $B","Profit Margin %","ROE (%)","ROA (%)","Debt/Equity","Current Ratio"]]
st.dataframe(prof_df, use_container_width=True)
st.caption("ROE = Return on Equity | ROA = Return on Assets")
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("PE Ratio Comparison")
    st.bar_chart(df.set_index("Company")["PE Ratio"])

with col2:
    st.subheader("Profit Margin % Comparison")
    st.bar_chart(df.set_index("Company")["Profit Margin %"])

col3, col4 = st.columns(2)

with col3:
    st.subheader("Revenue $B Comparison")
    st.bar_chart(df.set_index("Company")["Revenue $B"])

with col4:
    st.subheader("ROE % Comparison")
    st.bar_chart(df.set_index("Company")["ROE (%)"])

st.divider()

st.subheader("Stock Price History")
selected = st.selectbox("Select Company", list(companies.keys()))
period = st.radio("Period", ["1mo","3mo","6mo","1y","2y","5y"], horizontal=True)
history = yf.Ticker(companies[selected]).history(period=period)
st.line_chart(history["Close"])
st.divider()

st.subheader("Compare Two Companies")
col5, col6 = st.columns(2)
with col5:
    comp1 = st.selectbox("Company 1", list(companies.keys()), index=0)
with col6:
    comp2 = st.selectbox("Company 2", list(companies.keys()), index=1)

h1 = yf.Ticker(companies[comp1]).history(period="1y")["Close"]
h2 = yf.Ticker(companies[comp2]).history(period="1y")["Close"]
compare_df = pd.DataFrame({comp1: h1, comp2: h2})
st.line_chart(compare_df)
