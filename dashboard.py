import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import pytz
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from textblob import TextBlob

chicago = pytz.timezone("America/Chicago")
now = datetime.now(chicago)

st.set_page_config(page_title="Stock Dashboard", page_icon="📈", layout="wide")

st.markdown('''
<style>
    .hero { padding: 20px 0px; }
    .kpi-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #2e3250;
    }
    .positive { color: #00d4aa; font-weight: bold; }
    .negative { color: #ff4b4b; font-weight: bold; }
    .stMetric { background: #1e2130; border-radius: 10px; padding: 10px; }
    footer { text-align: center; color: #888; margin-top: 40px; }
</style>
''', unsafe_allow_html=True)

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

with st.sidebar:
    st.image("https://img.icons8.com/fluency/48/stock-share.png", width=48)
    st.title("Dashboard Controls")
    st.divider()
    selected_company = st.selectbox("Select Company", list(companies.keys()))
    selected_ticker  = companies[selected_company]
    period = st.radio("Time Period", ["1mo","3mo","6mo","1y","2y","5y"], index=3)
    st.divider()
    st.subheader("Technical Indicators")
    show_sma20  = st.checkbox("SMA 20",  value=True)
    show_sma50  = st.checkbox("SMA 50",  value=True)
    show_sma200 = st.checkbox("SMA 200", value=False)
    show_ema    = st.checkbox("EMA 20",  value=False)
    show_rsi    = st.checkbox("RSI",     value=True)
    show_macd   = st.checkbox("MACD",    value=True)
    show_volume = st.checkbox("Volume",  value=True)
    st.divider()
    st.caption("Built by Poonam Dhanuka")
    st.caption("DePaul MS Finance 2027")
    st.caption("Data: Yahoo Finance")

@st.cache_data(ttl=3600)
def get_history(ticker, period):
    df = yf.Ticker(ticker).history(period=period)
    df.index = df.index.tz_localize(None)
    return df

@st.cache_data(ttl=3600)
def get_info(ticker):
    return yf.Ticker(ticker).info

@st.cache_data(ttl=3600)
def get_all_stocks():
    data = []
    for name, ticker in companies.items():
        try:
            info = yf.Ticker(ticker).info
            price = info.get("currentPrice", 0)
            prev  = info.get("previousClose", price)
            change = round(price - prev, 2)
            pct    = round((change / prev) * 100, 2) if prev else 0
            data.append({
                "Company": name, "Ticker": ticker,
                "Price ($)": price, "Change (%)": pct,
                "Market Cap $B": round(info.get("marketCap", 0)/1e9, 2),
                "Revenue $B":    round(info.get("totalRevenue", 0)/1e9, 2),
                "PE Ratio":      round(info.get("trailingPE", 0), 2),
                "Forward PE":    round(info.get("forwardPE", 0), 2),
                "PB Ratio":      round(info.get("priceToBook", 0), 2),
                "PS Ratio":      round(info.get("priceToSalesTrailing12Months", 0), 2),
                "EPS ($)":       round(info.get("trailingEps", 0), 2),
                "Beta":          round(info.get("beta", 0), 2),
                "ROE (%)":       round(info.get("returnOnEquity", 0)*100, 2),
                "ROA (%)":       round(info.get("returnOnAssets", 0)*100, 2),
                "ROI (%)":       round(info.get("returnOnEquity", 0)*100, 2),
                "Profit Margin %": round(info.get("profitMargins", 0)*100, 2),
                "Gross Margin %":  round(info.get("grossMargins", 0)*100, 2),
                "Op Margin %":     round(info.get("operatingMargins", 0)*100, 2),
                "Debt/Equity":   round(info.get("debtToEquity", 0), 2),
                "Current Ratio": round(info.get("currentRatio", 0), 2),
                "Quick Ratio":   round(info.get("quickRatio", 0), 2),
                "Div Yield (%)": round(info.get("dividendYield", 0)*100, 2),
                "52W High ($)":  info.get("fiftyTwoWeekHigh", 0),
                "52W Low ($)":   info.get("fiftyTwoWeekLow", 0),
                "EV $B":         round(info.get("enterpriseValue", 0)/1e9, 2),
                "EBITDA $B":     round(info.get("ebitda", 0)/1e9, 2),
                "Free CF $B":    round(info.get("freeCashflow", 0)/1e9, 2),
                "Target Price ($)": round(info.get("targetMeanPrice", 0), 2),
                "Analyst Rating":   info.get("recommendationKey", "N/A").upper(),
                "Employees":     info.get("fullTimeEmployees", 0),
                "HQ":            info.get("city","") + ", " + info.get("state",""),
                "Website":       info.get("website", "N/A"),
                "Sector":        info.get("sector", "N/A"),
                "Industry":      info.get("industry", "N/A"),
                "Description":   info.get("longBusinessSummary", "N/A"),
            })
            time.sleep(0.5)
        except:
            pass
    return pd.DataFrame(data)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd  = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

with st.spinner("Loading market data..."):
    history = get_history(selected_ticker, period)
    info    = get_info(selected_ticker)
    df_all  = get_all_stocks()

st.markdown('<div class="hero">', unsafe_allow_html=True)
st.title("Live Stock Market Dashboard")
st.markdown(f"**{selected_company} ({selected_ticker})** | {now.strftime('%B %d, %Y %I:%M %p')} CST")
st.markdown('</div>', unsafe_allow_html=True)
st.divider()

price    = info.get("currentPrice", 0)
prev     = info.get("previousClose", price)
change   = round(price - prev, 2)
pct      = round((change / prev) * 100, 2) if prev else 0
mktcap   = round(info.get("marketCap", 0)/1e9, 2)
high52   = info.get("fiftyTwoWeekHigh", 0)
low52    = info.get("fiftyTwoWeekLow", 0)
volume   = info.get("volume", 0)
avg_vol  = info.get("averageVolume", 0)
target   = info.get("targetMeanPrice", 0)
rating   = info.get("recommendationKey", "N/A").upper()

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Price",        f"${price}",     f"{pct}%")
c2.metric("Market Cap",   f"${mktcap}B")
c3.metric("52W High",     f"${high52}")
c4.metric("52W Low",      f"${low52}")
c5.metric("Target Price", f"${target}")
c6.metric("Analyst",      rating)
st.divider()

tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = st.tabs([
    "Candlestick","Technical","Fundamentals",
    "Company Info","News & Sentiment",
    "Comparison","Forecast","Portfolio","Market Overview"
])

with tab1:
    st.subheader(f"{selected_company} - Candlestick Chart")
    fig = make_subplots(rows=2 if show_volume else 1, cols=1,
                        shared_xaxes=True, row_heights=[0.7,0.3] if show_volume else [1])
    fig.add_trace(go.Candlestick(
        x=history.index, open=history["Open"], high=history["High"],
        low=history["Low"], close=history["Close"], name="OHLC",
        increasing_line_color="#00d4aa", decreasing_line_color="#ff4b4b"
    ), row=1, col=1)
    if show_sma20:
        fig.add_trace(go.Scatter(x=history.index, y=history["Close"].rolling(20).mean(),
            name="SMA 20", line=dict(color="#ffd700", width=1)), row=1, col=1)
    if show_sma50:
        fig.add_trace(go.Scatter(x=history.index, y=history["Close"].rolling(50).mean(),
            name="SMA 50", line=dict(color="#ff8c00", width=1)), row=1, col=1)
    if show_sma200:
        fig.add_trace(go.Scatter(x=history.index, y=history["Close"].rolling(200).mean(),
            name="SMA 200", line=dict(color="#9370db", width=1)), row=1, col=1)
    if show_ema:
        fig.add_trace(go.Scatter(x=history.index, y=history["Close"].ewm(span=20).mean(),
            name="EMA 20", line=dict(color="#00bfff", width=1, dash="dash")), row=1, col=1)
    if show_volume:
        colors = ["#00d4aa" if c >= o else "#ff4b4b"
                  for c,o in zip(history["Close"], history["Open"])]
        fig.add_trace(go.Bar(x=history.index, y=history["Volume"],
            name="Volume", marker_color=colors), row=2, col=1)
    fig.update_layout(height=600, template="plotly_dark",
                      xaxis_rangeslider_visible=False,
                      paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Technical Indicators")
    rsi  = compute_rsi(history["Close"])
    macd, signal = compute_macd(history["Close"])
    rows = sum([show_rsi, show_macd]) + 1
    fig2 = make_subplots(rows=rows, cols=1, shared_xaxes=True,
                         subplot_titles=["Price"] + (["RSI"] if show_rsi else []) + (["MACD"] if show_macd else []))
    fig2.add_trace(go.Scatter(x=history.index, y=history["Close"],
        name="Price", line=dict(color="#00d4aa")), row=1, col=1)
    row_idx = 2
    if show_rsi:
        fig2.add_trace(go.Scatter(x=history.index, y=rsi,
            name="RSI", line=dict(color="#ffd700")), row=row_idx, col=1)
        fig2.add_hline(y=70, line_color="red",   line_dash="dash", row=row_idx, col=1)
        fig2.add_hline(y=30, line_color="green", line_dash="dash", row=row_idx, col=1)
        row_idx += 1
    if show_macd:
        fig2.add_trace(go.Scatter(x=history.index, y=macd,
            name="MACD", line=dict(color="#00bfff")), row=row_idx, col=1)
        fig2.add_trace(go.Scatter(x=history.index, y=signal,
            name="Signal", line=dict(color="#ff8c00")), row=row_idx, col=1)
    fig2.update_layout(height=700, template="plotly_dark",
                       paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("RSI > 70 = Overbought (may drop) | RSI < 30 = Oversold (may rise) | MACD crosses signal = buy/sell signal")

with tab3:
    def color(val):
        if isinstance(val, (int, float)):
            c = "green" if val > 0 else "red"
            return f"color: {c}; font-weight: bold"
        return ""
    st.subheader("Valuation Ratios")
    val_df = df_all[["Company","PE Ratio","Forward PE","PB Ratio","PS Ratio","EPS ($)","EV $B","EBITDA $B"]]
    st.dataframe(val_df, use_container_width=True, height=380)
    st.caption("PE=Price/Earnings | PB=Price/Book | PS=Price/Sales | EV=Enterprise Value")
    st.subheader("Profitability")
    prof_df = df_all[["Company","Revenue $B","Profit Margin %","Gross Margin %","Op Margin %","ROE (%)","ROA (%)","Free CF $B"]]
    st.dataframe(prof_df.style.map(color, subset=["Profit Margin %","ROE (%)","ROA (%)"]), use_container_width=True, height=380)
    st.subheader("Financial Health")
    health_df = df_all[["Company","Debt/Equity","Current Ratio","Quick Ratio","Beta","Div Yield (%)","Employees"]]
    st.dataframe(health_df, use_container_width=True, height=380)
    csv = df_all.to_csv(index=False).encode("utf-8")
    st.download_button("Download All Data as CSV", csv, "stocks.csv", "text/csv")

with tab4:
    st.subheader("Company Information")
    row = df_all[df_all["Company"] == selected_company].iloc[0]
    col1,col2,col3 = st.columns(3)
    with col1:
        st.markdown("**Headquarters**"); st.write(row["HQ"])
        st.markdown("**Sector**");       st.write(row["Sector"])
    with col2:
        st.markdown("**Industry**");   st.write(row["Industry"])
        st.markdown("**Employees**");  st.write(f"{int(row['Employees']):,}")
    with col3:
        st.markdown("**Website**");        st.write(row["Website"])
        st.markdown("**Analyst Rating**"); st.write(row["Analyst Rating"])
    st.divider()
    st.markdown("**About**")
    st.write(row["Description"])

with tab5:
    st.subheader("Latest News & Sentiment")
    try:
        news_items = yf.Ticker(selected_ticker).news[:10]
        sentiments = []
        for article in news_items:
            content  = article.get("content", {})
            title    = content.get("title", "No title")
            summary  = content.get("summary", "")
            pub      = content.get("pubDate", "")
            link     = content.get("canonicalUrl", {}).get("url", "#")
            polarity = TextBlob(title).sentiment.polarity
            sentiments.append(polarity)
            if polarity > 0.1:
                sentiment_label = "Positive"
                sentiment_color = "green"
            elif polarity < -0.1:
                sentiment_label = "Negative"
                sentiment_color = "red"
            else:
                sentiment_label = "Neutral"
                sentiment_color = "gray"
            st.markdown(f"**[{title}]({link})**")
            col_s1, col_s2 = st.columns([3,1])
            with col_s1:
                if summary:
                    st.write(summary[:200] + "...")
                st.caption(pub)
            with col_s2:
                st.markdown(f'<span style="color:{sentiment_color};font-weight:bold">{sentiment_label}</span>', unsafe_allow_html=True)
                st.write(f"Score: {round(polarity,2)}")
            st.divider()
        avg_sentiment = sum(sentiments)/len(sentiments) if sentiments else 0
        st.metric("Overall News Sentiment", 
                  "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral",
                  f"Score: {round(avg_sentiment,3)}")
    except:
        st.write("News not available right now.")

with tab6:
    st.subheader("Compare Companies")
    selected_comps = st.multiselect("Select Companies to Compare",
                                    list(companies.keys()),
                                    default=["Nike","Apple","Microsoft"])
    if selected_comps:
        comp_hist = {}
        for c in selected_comps:
            h = get_history(companies[c], period)
            comp_hist[c] = h["Close"]
        comp_df = pd.DataFrame(comp_hist)
        norm_df = (comp_df / comp_df.iloc[0]) * 100
        fig3 = go.Figure()
        colors_list = ["#00d4aa","#ffd700","#ff4b4b","#00bfff","#ff8c00"]
        for i, c in enumerate(selected_comps):
            fig3.add_trace(go.Scatter(x=norm_df.index, y=norm_df[c],
                name=c, line=dict(color=colors_list[i % len(colors_list)])))
        fig3.update_layout(title="Normalized Price Performance (Base=100)",
                           template="plotly_dark", height=500,
                           paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
        st.plotly_chart(fig3, use_container_width=True)
        st.subheader("Return Comparison")
        returns = {}
        for c in selected_comps:
            h = comp_hist[c]
            ret = round(((h.iloc[-1] - h.iloc[0]) / h.iloc[0]) * 100, 2)
            returns[c] = ret
        ret_df = pd.DataFrame(list(returns.items()), columns=["Company","Return (%)"])
        ret_df = ret_df.sort_values("Return (%)", ascending=False)
        st.dataframe(ret_df, use_container_width=True)
        st.bar_chart(ret_df.set_index("Company")["Return (%)"])

with tab7:
    st.subheader(f"{selected_company} - 30 Day Price Forecast")
    st.caption("Educational use only. Not financial advice.")
    close_prices = history["Close"].dropna().values
    X = np.arange(len(close_prices)).reshape(-1,1)
    y = close_prices
    model = LinearRegression().fit(X, y)
    future_X = np.arange(len(close_prices), len(close_prices)+30).reshape(-1,1)
    forecast = model.predict(future_X)
    last_date = history.index[-1]
    future_dates = pd.date_range(last_date, periods=31, freq="B")[1:]
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=history.index, y=history["Close"],
        name="Historical", line=dict(color="#00d4aa")))
    fig4.add_trace(go.Scatter(x=future_dates, y=forecast,
        name="Forecast", line=dict(color="#ffd700", dash="dash")))
    fig4.update_layout(title="30-Day Linear Regression Forecast",
                       template="plotly_dark", height=500,
                       paper_bgcolor="#0e1117", plot_bgcolor="#0e1117")
    st.plotly_chart(fig4, use_container_width=True)
    direction = "UP" if forecast[-1] > close_prices[-1] else "DOWN"
    pct_change = round(((forecast[-1] - close_prices[-1]) / close_prices[-1]) * 100, 2)
    st.metric("30-Day Forecast Direction", direction, f"{pct_change}%")

with tab8:
    st.subheader("Portfolio Simulator")
    st.write("Select stocks and allocate weights to simulate your portfolio.")
    port_stocks = st.multiselect("Select Stocks", list(companies.keys()),
                                 default=["Nike","Apple","Microsoft","Tesla"])
    if port_stocks:
        weights = []
        cols_port = st.columns(len(port_stocks))
        for i, stock in enumerate(port_stocks):
            with cols_port[i]:
                w = st.number_input(f"{stock} %", 0, 100,
                                    value=round(100//len(port_stocks)), key=f"w_{stock}")
                weights.append(w)
        total_weight = sum(weights)
        st.write(f"Total Allocation: {total_weight}%")
        if total_weight == 100:
            port_returns = []
            port_vols    = []
            for stock, w in zip(port_stocks, weights):
                h = get_history(companies[stock], "1y")["Close"]
                ret = ((h.iloc[-1] - h.iloc[0]) / h.iloc[0]) * 100
                vol = h.pct_change().std() * (252**0.5) * 100
                port_returns.append(ret * w/100)
                port_vols.append(vol * w/100)
            total_return = round(sum(port_returns), 2)
            total_vol    = round(sum(port_vols), 2)
            sharpe       = round(total_return / total_vol, 2) if total_vol else 0
            c1,c2,c3 = st.columns(3)
            c1.metric("Portfolio Return (1Y)", f"{total_return}%")
            c2.metric("Portfolio Volatility",  f"{total_vol}%")
            c3.metric("Sharpe Ratio (approx)", sharpe)
            port_df = pd.DataFrame({
                "Stock": port_stocks,
                "Weight (%)": weights,
                "Contribution to Return (%)": [round(r,2) for r in port_returns]
            })
            st.dataframe(port_df, use_container_width=True)
        else:
            st.warning(f"Weights must add up to 100%. Currently: {total_weight}%")

with tab9:
    st.subheader('Market Overview - Top Movers Today')
    gainers = df_all.nlargest(5, 'Change (%)')
    losers  = df_all.nsmallest(5, 'Change (%)')
    col_g, col_l = st.columns(2)
    with col_g:
        st.markdown('### Top Gainers')
        for _, row in gainers.iterrows():
            st.metric(row['Company'], f"${row['Price ($)']}", f"+{row['Change (%)']}%")
    with col_l:
        st.markdown('### Top Losers')
        for _, row in losers.iterrows():
            st.metric(row['Company'], f"${row['Price ($)']}", f"{row['Change (%)']}%")
    st.divider()
    st.subheader('All Companies Overview')
    def color2(val):
        if isinstance(val, (int, float)):
            c = 'green' if val > 0 else 'red'
            return f'color: {c}; font-weight: bold'
        return ''
    overview = df_all[['Company','Ticker','Price ($)','Change (%)','Market Cap $B','PE Ratio','Analyst Rating']]
    st.dataframe(overview.style.map(color2, subset=['Change (%)']), use_container_width=True, height=400)

st.divider()
st.markdown('<footer style="text-align:center; color:#888; padding:20px">Built by <b>Poonam Dhanuka</b> | DePaul University MS Finance 2027 | Data: Yahoo Finance</footer>', unsafe_allow_html=True)
