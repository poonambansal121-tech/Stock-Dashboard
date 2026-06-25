import streamlit as st
import yfinance as yf
import pandas as pd
import time
import pytz
from datetime import datetime

chicago = pytz.timezone("America/Chicago")
now = datetime.now(chicago)

st.set_page_config(page_title="Stock Dashboard", page_icon="📈", layout="wide")

st.markdown('''
<style>
    .main { background-color: #0e1117; }
    h1 { color: #00d4aa !important; }
    h2, h3 { color: #ffffff !important; }
</style>
''', unsafe_allow_html=True)

st.title("Live Stock Dashboard")
st.write("Updated: " + now.strftime("%B %d, %Y %I:%M %p") + " CST")
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
                "Company":          name,
                "Ticker":           ticker,
                "Price ($)":        price,
                "Change (%)":       pct,
                "Market Cap $B":    round(info.get("marketCap", 0) / 1e9, 2),
                "Revenue $B":       round(info.get("totalRevenue", 0) / 1e9, 2),
                "PE Ratio":         round(info.get("trailingPE", 0), 2),
                "Forward PE":       round(info.get("forwardPE", 0), 2),
                "PB Ratio":         round(info.get("priceToBook", 0), 2),
                "PS Ratio":         round(info.get("priceToSalesTrailing12Months", 0), 2),
                "EPS ($)":          round(info.get("trailingEps", 0), 2),
                "Beta":             round(info.get("beta", 0), 2),
                "ROE (%)":          round(info.get("returnOnEquity", 0) * 100, 2),
                "ROA (%)":          round(info.get("returnOnAssets", 0) * 100, 2),
                "ROI (%)":          round(info.get("returnOnEquity", 0) * 100, 2),
                "Profit Margin %":  round(info.get("profitMargins", 0) * 100, 2),
                "Gross Margin %":   round(info.get("grossMargins", 0) * 100, 2),
                "Op Margin %":      round(info.get("operatingMargins", 0) * 100, 2),
                "Debt/Equity":      round(info.get("debtToEquity", 0), 2),
                "Current Ratio":    round(info.get("currentRatio", 0), 2),
                "Quick Ratio":      round(info.get("quickRatio", 0), 2),
                "Div Yield (%)":    round(info.get("dividendYield", 0) * 100, 2),
                "52W High ($)":     info.get("fiftyTwoWeekHigh", 0),
                "52W Low ($)":      info.get("fiftyTwoWeekLow", 0),
                "EV $B":            round(info.get("enterpriseValue", 0) / 1e9, 2),
                "EBITDA $B":        round(info.get("ebitda", 0) / 1e9, 2),
                "Free CF $B":       round(info.get("freeCashflow", 0) / 1e9, 2),
                "Target Price ($)": round(info.get("targetMeanPrice", 0), 2),
                "Analyst Rating":   info.get("recommendationKey", "N/A").upper(),
                "Employees":        info.get("fullTimeEmployees", 0),
                "HQ":               info.get("city", "") + ", " + info.get("state", ""),
                "Website":          info.get("website", "N/A"),
                "Sector":           info.get("sector", "N/A"),
                "Industry":         info.get("industry", "N/A"),
                "Description":      info.get("longBusinessSummary", "N/A"),
            })
            time.sleep(0.5)
        except:
            pass
    return pd.DataFrame(data)

with st.spinner("Loading live market data..."):
    df = get_stock_data()

st.subheader("Market Snapshot")
cols = st.columns(5)
top5 = df.nlargest(5, "Market Cap $B")
for i, (_, row) in enumerate(top5.iterrows()):
    with cols[i]:
        st.metric(
            label=row["Company"],
            value=f"${row['Price ($)']}",
            delta=f"{row['Change (%)']}%"
        )
st.divider()

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Live Prices",
    "Valuation",
    "Profitability",
    "Financial Health",
    "Company Info",
    "News",
    "Charts"
])

def color(val):
    if isinstance(val, (int, float)):
        c = "green" if val > 0 else "red"
        return f"color: {c}; font-weight: bold"
    return ""

with tab1:
    st.subheader("Live Stock Prices")
    price_df = df[["Company","Price ($)","Change (%)","Market Cap $B","52W High ($)","52W Low ($)","Target Price ($)","Analyst Rating"]]
    st.dataframe(price_df.style.map(color, subset=["Change (%)"]), use_container_width=True, height=400)

with tab2:
    st.subheader("Valuation Ratios")
    val_df = df[["Company","PE Ratio","Forward PE","PB Ratio","PS Ratio","EPS ($)","EV $B","EBITDA $B"]]
    st.dataframe(val_df, use_container_width=True, height=400)
    st.caption("PE=Price/Earnings | PB=Price/Book | PS=Price/Sales | EV=Enterprise Value")

with tab3:
    st.subheader("Profitability")
    prof_df = df[["Company","Revenue $B","Profit Margin %","Gross Margin %","Op Margin %","ROE (%)","ROA (%)","ROI (%)","Free CF $B"]]
    st.dataframe(prof_df.style.map(color, subset=["Profit Margin %","Gross Margin %","Op Margin %","ROE (%)","ROA (%)"]), use_container_width=True, height=400)

with tab4:
    st.subheader("Financial Health")
    health_df = df[["Company","Debt/Equity","Current Ratio","Quick Ratio","Beta","Div Yield (%)","Employees"]]
    st.dataframe(health_df, use_container_width=True, height=400)
    st.caption("Beta > 1 = more volatile than market | Current Ratio > 1 = financially healthy")

with tab5:
    st.subheader("Company Information")
    selected_co = st.selectbox("Select Company", list(companies.keys()), key="info_select")
    row = df[df["Company"] == selected_co].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Headquarters**")
        st.write(row["HQ"])
        st.markdown("**Sector**")
        st.write(row["Sector"])
    with col2:
        st.markdown("**Industry**")
        st.write(row["Industry"])
        st.markdown("**Employees**")
        st.write(f"{int(row['Employees']):,}")
    with col3:
        st.markdown("**Website**")
        st.write(row["Website"])
        st.markdown("**Analyst Rating**")
        st.write(row["Analyst Rating"])

    st.divider()
    st.markdown("**About the Company**")
    st.write(row["Description"])

with tab6:
    st.subheader("Latest News")
    news_co = st.selectbox("Select Company", list(companies.keys()), key="news_select")
    try:
        news = yf.Ticker(companies[news_co]).news[:8]
        for article in news:
            content = article.get("content", {})
            title   = content.get("title", "No title")
            summary = content.get("summary", "")
            pub     = content.get("pubDate", "")
            link    = content.get("canonicalUrl", {}).get("url", "#")
            st.markdown(f"**[{title}]({link})**")
            if summary:
                st.write(summary[:200] + "...")
            st.caption(pub)
            st.divider()
    except:
        st.write("News not available right now.")

with tab7:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("PE Ratio")
        st.bar_chart(df.set_index("Company")["PE Ratio"])
    with col2:
        st.subheader("Profit Margin %")
        st.bar_chart(df.set_index("Company")["Profit Margin %"])

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Revenue $B")
        st.bar_chart(df.set_index("Company")["Revenue $B"])
    with col4:
        st.subheader("Beta (Volatility)")
        st.bar_chart(df.set_index("Company")["Beta"])

    st.divider()
    st.subheader("Stock Price History")
    col_a, col_b = st.columns([2,3])
    with col_a:
        selected = st.selectbox("Select Company", list(companies.keys()), key="hist_select")
    with col_b:
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

st.divider()
st.caption("Built by Poonam Dhanuka | DePaul MS Finance
