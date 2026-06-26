import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import pytz
from datetime import datetime
from sklearn.linear_model import LinearRegression
from config import COMPANIES, DEFAULT_PERIOD
from data import fetch_history, fetch_info, fetch_news, fetch_all_stocks
from charts import candlestick_chart, indicator_chart, comparison_chart
from utils import format_number, color_value, get_sentiment

chicago = pytz.timezone('America/Chicago')
now = datetime.now(chicago)

st.set_page_config(page_title='Stock Dashboard', page_icon='📈', layout='wide')

# ── YAHOO FINANCE DARK THEME ──────────────────────────────────────────────────
st.markdown('''
<style>
/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, sans-serif;
}
.stApp {
    background-color: #0f0f0f;
    color: #e0e0e0;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background-color: #111111 !important;
    border-right: 1px solid #222 !important;
}
section[data-testid="stSidebar"] * { color: #ccc !important; }
section[data-testid="stSidebar"] .stRadio label { color: #ccc !important; }
section[data-testid="stSidebar"] hr { border-color: #333 !important; }

/* ── Top navbar banner ── */
.yf-navbar {
    background: #111;
    border-bottom: 2px solid #6001d2;
    padding: 10px 0 8px 0;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.yf-brand {
    font-size: 20px;
    font-weight: 900;
    color: #6001d2;
    letter-spacing: -0.5px;
}
.yf-brand span { color: #fff; }
.yf-tagline { color: #555; font-size: 12px; }

/* ── Hero price card ── */
.yf-hero {
    background: #141414;
    border: 1px solid #222;
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 18px;
}
.yf-company-name  { font-size: 12px; color: #777; letter-spacing: 0.3px; margin-bottom: 4px; }
.yf-sector-line   { font-size: 12px; color: #555; margin-top: 2px; }
.yf-price         { font-size: 40px; font-weight: 800; color: #fff; line-height: 1.1; }
.yf-change-up     { color: #00c878; font-size: 17px; font-weight: 700; }
.yf-change-down   { color: #ff4b4b; font-size: 17px; font-weight: 700; }
.yf-timestamp     { font-size: 11px; color: #444; margin-top: 6px; }

/* ── KPI / metric card ── */
.yf-kpi {
    background: #141414;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.yf-kpi:hover { border-color: #6001d2; }
.yf-kpi-label { font-size: 10px; color: #aaa; text-transform: uppercase; letter-spacing: 0.6px; }
.yf-kpi-value { font-size: 17px; font-weight: 700; color: #fff; margin-top: 3px; }

/* ── Section title ── */
.yf-section {
    font-size: 15px;
    font-weight: 700;
    color: #fff;
    border-left: 3px solid #6001d2;
    padding-left: 10px;
    margin: 20px 0 12px 0;
}

/* ── News card ── */
.yf-news {
    background: #141414;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.yf-news:hover { border-color: #6001d2; }

/* ── Positive / Negative colours ── */
.positive { color: #00c878 !important; font-weight: bold; }
.negative { color: #ff4b4b !important; font-weight: bold; }

/* ── Streamlit metric overrides ── */
[data-testid="metric-container"] {
    background: #141414;
    border: 1px solid #222;
    border-radius: 10px;
    padding: 14px 16px !important;
}
[data-testid="metric-container"] label { color: #888 !important; font-size: 11px !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #fff !important; font-weight: 700 !important; }
[data-testid="metric-container"] [data-testid="stMetricDelta"] svg { display: none; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: #141414; border-radius: 8px; gap: 4px; }
.stTabs [data-baseweb="tab"]      { color: #888 !important; border-radius: 6px; }
.stTabs [aria-selected="true"]    { background: #6001d2 !important; color: #fff !important; }

/* ── Buttons ── */
.stButton > button {
    background: #6001d2 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { background: #7b22e8 !important; }

/* ── Download button ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid #333 !important;
    color: #aaa !important;
    border-radius: 8px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Divider ── */
hr { border-color: #222 !important; }

/* ── Inputs / sliders ── */
.stSlider [data-baseweb="slider"] div[role="slider"] { background: #6001d2 !important; }
.stTextInput input, .stNumberInput input, .stSelectbox select {
    background: #1a1a1a !important;
    color: #fff !important;
    border-color: #333 !important;
    border-radius: 8px !important;
}

/* ── White labels in company-selection bar ── */
.stRadio label,
.stRadio [data-baseweb="radio"] + div,
.stRadio > div > label,
div[data-testid="stRadio"] label,
div[data-testid="stRadio"] > label { color: #fff !important; }
div[data-testid="stRadio"] p { color: #fff !important; }
.stTextInput label, .stTextInput label p { color: #fff !important; }
.stSelectbox label, .stSelectbox label p { color: #fff !important; }
.stSlider label, .stSlider label p { color: #fff !important; }
[data-testid="stSelectSlider"] label,
[data-testid="stSelectSlider"] label p { color: #fff !important; }
</style>
''', unsafe_allow_html=True)

# ── DARK PLOTLY TEMPLATE (shared across all inline charts) ────────────────────
DARK_LAYOUT = dict(
    paper_bgcolor='#111',
    plot_bgcolor='#111',
    font=dict(color='#aaa', size=12),
    xaxis=dict(showgrid=False, color='#444', zeroline=False),
    yaxis=dict(gridcolor='#222', color='#aaa', zeroline=False),
    margin=dict(l=10, r=10, t=40, b=10),
)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('## 📈 StockPro')
    st.markdown('<span style="color:#888;font-size:12px">Built by Poonam Dhanuka<br>DePaul MS Finance 2027</span>',
                unsafe_allow_html=True)
    st.divider()
    page = st.radio('Navigate', [
        'Overview',
        'Historical Price',
        'Technical Indicators',
        'Financial Metrics',
        'Company Info',
        'Latest News',
        'Stock Comparison',
        'Portfolio Tracker',
        'Price Forecast',
        'Correlation Heatmap',
        'Monte Carlo',
        'Stock Screener',
        'Market Sentiment',
        'Market Overview'
    ])
    st.divider()
    st.caption('Data: Yahoo Finance')
    st.caption(now.strftime('%b %d, %Y %I:%M %p') + ' CST')

# ── COMPANY SELECTION BAR (top of main page) ─────────────────────────────────
st.markdown('''
<div style="background:#141414; border:1px solid #333; border-radius:12px;
            padding:14px 20px; margin-bottom:16px;">
''', unsafe_allow_html=True)

col_mode, col_pick, col_period = st.columns([1, 2, 1])
with col_mode:
    mode = st.radio('Pick Stock', ['From List', 'Enter Any Ticker'], horizontal=True)
with col_pick:
    if mode == 'Enter Any Ticker':
        custom = st.text_input('Ticker Symbol (e.g. GOOGL, V, META)', '').upper().strip()
        selected_ticker  = custom if custom else 'AAPL'
        selected_company = selected_ticker
    else:
        selected_company = st.selectbox('Select Company', list(COMPANIES.keys()))
        selected_ticker  = COMPANIES[selected_company]
with col_period:
    period = st.select_slider('Time Period',
        options=['1mo','3mo','6mo','1y','2y','5y'], value='1y')

st.markdown('</div>', unsafe_allow_html=True)

# ── LOAD DATA ────────────────────────────────────────────────────────────────
with st.spinner('Fetching data...'):
    try:
        history = fetch_history(selected_ticker, period)
        info    = fetch_info(selected_ticker)
        price    = info.get('currentPrice', 0)
        prev     = info.get('previousClose', price)
        change   = round(price - prev, 2)
        pct      = round((change/prev)*100, 2) if prev else 0
        mktcap   = info.get('marketCap', 0)
        high52   = info.get('fiftyTwoWeekHigh', 0)
        low52    = info.get('fiftyTwoWeekLow', 0)
        target   = info.get('targetMeanPrice', 0)
        rating   = info.get('recommendationKey', 'N/A').upper()
        pe       = round(info.get('trailingPE', 0), 2)
        div      = round(info.get('dividendYield', 0)*100, 2)
        beta     = round(info.get('beta', 0), 2)
        data_ok  = True
    except Exception as e:
        st.error(f'Could not load data for {selected_ticker}. Please try again.')
        data_ok = False

if not data_ok:
    st.stop()

# ── NAVBAR ────────────────────────────────────────────────────────────────────
st.markdown(f'''
<div class="yf-navbar">
    <div class="yf-brand">Stock<span>Pro</span></div>
    <div style="color:#333">|</div>
    <div style="color:#fff;font-weight:600;font-size:14px">{selected_ticker}</div>
    <div class="yf-tagline">Real-time market data · Yahoo Finance</div>
</div>
''', unsafe_allow_html=True)

# ── HERO PRICE HEADER ─────────────────────────────────────────────────────────
logo        = info.get('logo_url', '')
sector      = info.get('sector', '')
industry    = info.get('industry', '')
city        = info.get('city', '')
state       = info.get('state', '')
exchange    = info.get('exchange', '')
chg_cls     = 'yf-change-up' if pct >= 0 else 'yf-change-down'
arrow       = '▲' if pct >= 0 else '▼'
mkt_time    = now.strftime('%b %d, %Y · %I:%M %p CST')

# Hero — full width
if logo:
    st.image(logo, width=48)
st.markdown(f'''
<div class="yf-hero">
    <div class="yf-company-name">{selected_company} · {exchange}</div>
    <div class="yf-sector-line">{sector} | {industry} | {city}, {state}</div>
    <div style="display:flex;align-items:baseline;gap:16px;margin-top:10px">
        <div class="yf-price">${price:,.2f}</div>
        <div class="{chg_cls}">{arrow} {abs(change):.2f} ({abs(pct):.2f}%)</div>
    </div>
    <div class="yf-timestamp">Currency in USD · {mkt_time}</div>
</div>
''', unsafe_allow_html=True)

# Quick Stats — horizontal row of 5 cards
st.markdown('<div class="yf-section">Quick Stats</div>', unsafe_allow_html=True)
rat_color = "#00c878" if rating in ("BUY","STRONG_BUY") else "#ff4b4b" if rating in ("SELL","STRONG_SELL") else "#f59e0b"
qs_cols = st.columns(5)
qs_data = [
    ("Market Cap",     format_number(mktcap, "$"), "#fff"),
    ("52-Week High",   f"${high52:,.2f}",          "#fff"),
    ("52-Week Low",    f"${low52:,.2f}",            "#fff"),
    ("Analyst Target", f"${target:,.2f}",           "#fff"),
    ("Rating",         rating,                      rat_color),
]
for col, (label, val, color) in zip(qs_cols, qs_data):
    with col:
        st.markdown(f'''
        <div class="yf-kpi" style="text-align:center">
            <div class="yf-kpi-label">{label}</div>
            <div class="yf-kpi-value" style="color:{color}">{val}</div>
        </div>''', unsafe_allow_html=True)

st.markdown('<hr>', unsafe_allow_html=True)

# ── OVERVIEW PAGE ─────────────────────────────────────────────────────────────
if page == 'Overview':
    st.markdown('<div class="yf-section">Financial Snapshot</div>', unsafe_allow_html=True)

    # ── Financial fundamentals (unique from Quick Stats above) ────
    vol         = info.get('volume', 0)
    avg_vol     = info.get('averageVolume', 0)
    profit_m    = round(info.get('profitMargins', 0) * 100, 2)
    eps_val     = info.get('trailingEps', 0)

    fin_cards = [
        ("PE Ratio",       f"{pe}x"             if pe else "N/A",   ""),
        ("EPS (TTM)",      f"${eps_val}"         if eps_val else "N/A", ""),
        ("Beta",           str(beta)             if beta else "N/A", ""),
        ("Div Yield",      f"{div}%"             if div else "N/A",  ""),
        ("Volume",         format_number(vol,""), ""),
        ("Profit Margin",  f"{profit_m}%"        if profit_m else "N/A", ""),
    ]
    cols_snap = st.columns(6)
    for col, (label, val, sub) in zip(cols_snap, fin_cards):
        with col:
            st.markdown(f"""
            <div style="background:#141414;border:1px solid #2a2a2a;border-radius:12px;
                        padding:16px 14px;text-align:center">
                <div style="font-size:10px;color:#aaa;text-transform:uppercase;
                            letter-spacing:0.7px;margin-bottom:6px">{label}</div>
                <div style="font-size:20px;font-weight:800;color:#fff">{val}</div>
                <div style="margin-top:4px;min-height:16px">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div style="margin:20px 0"></div>', unsafe_allow_html=True)

    # ── Chart + Key Metrics ───────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<div class="yf-section">Price Chart</div>', unsafe_allow_html=True)
        fig = candlestick_chart(history)
        fig.update_layout(**DARK_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="yf-section">Key Metrics</div>', unsafe_allow_html=True)
        metrics = [
            ("PE Ratio",      pe),
            ("Beta",          beta),
            ("Div Yield",     f"{div}%"),
            ("EPS",           f'${info.get("trailingEps",0)}'),
            ("Revenue",       format_number(info.get("totalRevenue",0),"$")),
            ("Profit Margin", f'{round(info.get("profitMargins",0)*100,2)}%'),
            ("ROE",           f'{round(info.get("returnOnEquity",0)*100,2)}%'),
            ("Debt / Equity", round(info.get("debtToEquity",0),2)),
        ]
        for k, v in metrics:
            st.markdown(f"""
            <div style="background:#141414;border:1px solid #2a2a2a;border-radius:10px;
                        padding:10px 14px;margin-bottom:8px;display:flex;
                        justify-content:space-between;align-items:center">
                <span style="font-size:11px;color:#aaa;text-transform:uppercase;
                             letter-spacing:0.5px">{k}</span>
                <span style="font-size:14px;font-weight:700;color:#fff">{v}</span>
            </div>""", unsafe_allow_html=True)

    csv = history.to_csv().encode('utf-8')
    st.download_button('⬇ Download Price Data as CSV',
                       csv, f'{selected_ticker}_prices.csv', 'text/csv')

# ── HISTORICAL PRICE PAGE ─────────────────────────────────────────────────────
elif page == 'Historical Price':
    st.markdown('<div class="yf-section">Historical Price Analysis</div>', unsafe_allow_html=True)
    col_opts = st.columns(5)
    with col_opts[0]: show_sma20  = st.checkbox('SMA 20',  True)
    with col_opts[1]: show_sma50  = st.checkbox('SMA 50',  True)
    with col_opts[2]: show_sma200 = st.checkbox('SMA 200', False)
    with col_opts[3]: show_ema    = st.checkbox('EMA 20',  False)
    with col_opts[4]: show_bb     = st.checkbox('Bollinger Bands', False)
    show_vol = st.checkbox('Volume Bars', True)
    fig = candlestick_chart(history, show_sma20, show_sma50,
                            show_sma200, show_ema, show_bb, show_vol)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('<div class="yf-section">Price Statistics</div>', unsafe_allow_html=True)
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric('Average Price', f'${round(history["Close"].mean(),2)}')
    col_s2.metric('Highest Price', f'${round(history["Close"].max(),2)}')
    col_s3.metric('Lowest Price',  f'${round(history["Close"].min(),2)}')
    col_s4.metric('Volatility',    f'{round(history["Close"].pct_change().std()*100,2)}%')
    csv = history.to_csv().encode('utf-8')
    st.download_button('⬇ Download Data as CSV',
                       csv, f'{selected_ticker}_history.csv', 'text/csv')

# ── TECHNICAL INDICATORS PAGE ─────────────────────────────────────────────────
elif page == 'Technical Indicators':
    st.markdown('<div class="yf-section">Technical Indicators</div>', unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1: show_rsi  = st.checkbox('RSI (14)',  True)
    with col_t2: show_macd = st.checkbox('MACD',      True)
    fig = indicator_chart(history, show_rsi, show_macd)
    st.plotly_chart(fig, use_container_width=True)
    st.caption('RSI > 70 = Overbought | RSI < 30 = Oversold | MACD cross = Buy/Sell signal')

# ── FINANCIAL METRICS PAGE ────────────────────────────────────────────────────
elif page == 'Financial Metrics':
    st.markdown('<div class="yf-section">Financial Metrics</div>', unsafe_allow_html=True)
    with st.spinner('Loading all company data...'):
        df_all = fetch_all_stocks()
    t1,t2,t3 = st.tabs(['Valuation','Profitability','Financial Health'])
    with t1:
        val_df = df_all[['Company','PE Ratio','Forward PE','PB Ratio','EPS ($)','Target Price ($)','Analyst Rating']]
        st.dataframe(val_df, use_container_width=True, height=400)
        st.caption('PE=Price/Earnings | PB=Price/Book | Forward PE uses estimated future earnings')
    with t2:
        prof_df = df_all[['Company','Revenue $B','Profit Margin %','Gross Margin %','ROE (%)','ROA (%)']]
        st.dataframe(prof_df.style.map(color_value,
            subset=['Profit Margin %','Gross Margin %','ROE (%)','ROA (%)']),
            use_container_width=True, height=400)
    with t3:
        health_df = df_all[['Company','Debt/Equity','Current Ratio','Quick Ratio','Beta','Div Yield (%)']]
        st.dataframe(health_df, use_container_width=True, height=400)
        st.caption('Current Ratio > 1 = Healthy | Beta > 1 = More volatile than market')
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button('⬇ Download All Metrics as CSV',
                       csv, 'all_stocks.csv', 'text/csv')

# ── COMPANY INFO PAGE ─────────────────────────────────────────────────────────
elif page == 'Company Info':
    st.markdown('<div class="yf-section">Company Information</div>', unsafe_allow_html=True)
    if logo:
        st.image(logo, width=80)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('**Headquarters**'); st.write(f"{info.get('city','')}, {info.get('state','')}")
        st.markdown('**Sector**');       st.write(info.get('sector','N/A'))
        st.markdown('**Industry**');     st.write(info.get('industry','N/A'))
    with col2:
        st.markdown('**Employees**'); st.write(f"{info.get('fullTimeEmployees',0):,}")
        st.markdown('**Website**');   st.write(info.get('website','N/A'))
        st.markdown('**Exchange**');  st.write(info.get('exchange','N/A'))
    with col3:
        st.markdown('**Market Cap**');    st.write(format_number(mktcap,'$'))
        st.markdown('**Analyst Rating**');st.write(rating)
        st.markdown('**Target Price**');  st.write(f'${target}')
    st.markdown('<hr>', unsafe_allow_html=True)
    st.markdown('**About the Company**')
    st.write(info.get('longBusinessSummary','N/A'))

# ── NEWS PAGE ─────────────────────────────────────────────────────────────────
elif page == 'Latest News':
    st.markdown('<div class="yf-section">Latest News & Sentiment</div>', unsafe_allow_html=True)
    try:
        news_items = fetch_news(selected_ticker)
        scores = []
        for article in news_items:
            content = article.get('content',{})
            title   = content.get('title','No title')
            summary = content.get('summary','')
            pub     = content.get('pubDate','')
            link    = content.get('canonicalUrl',{}).get('url','#')
            label, color, score = get_sentiment(title)
            scores.append(score)
            sentiment_color = '#00c878' if score > 0.1 else '#ff4b4b' if score < -0.1 else '#f59e0b'
            st.markdown(f'''
            <div class="yf-news">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div style="flex:1">
                        <a href="{link}" target="_blank"
                           style="font-size:14px;font-weight:600;color:#e0e0e0;text-decoration:none">
                            {title}
                        </a>
                        <div style="font-size:12px;color:#555;margin-top:4px">{summary[:180]+"..." if summary else ""}</div>
                        <div style="font-size:11px;color:#444;margin-top:6px">{pub}</div>
                    </div>
                    <div style="margin-left:16px;text-align:center;min-width:70px">
                        <div style="color:{sentiment_color};font-weight:700;font-size:12px">{label}</div>
                        <div style="color:#555;font-size:11px">{round(score,2)}</div>
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
        avg = sum(scores)/len(scores) if scores else 0
        overall = 'Positive' if avg > 0.1 else 'Negative' if avg < -0.1 else 'Neutral'
        overall_color = '#00c878' if avg > 0.1 else '#ff4b4b' if avg < -0.1 else '#f59e0b'
        st.markdown(f'''
        <div class="yf-kpi" style="margin-top:16px">
            <div class="yf-kpi-label">Overall Sentiment</div>
            <div class="yf-kpi-value" style="color:{overall_color}">{overall} · Score: {round(avg,3)}</div>
        </div>
        ''', unsafe_allow_html=True)
    except:
        st.warning('News not available right now. Please try again later.')

# ── COMPARISON PAGE ───────────────────────────────────────────────────────────
elif page == 'Stock Comparison':
    st.markdown('<div class="yf-section">Stock Comparison</div>', unsafe_allow_html=True)
    selected_comps = st.multiselect('Select Companies',
        list(COMPANIES.keys()), default=['Nike','Apple','Microsoft'])
    if selected_comps:
        stock_data = {}
        for c in selected_comps:
            h = fetch_history(COMPANIES[c], period)
            stock_data[c] = h['Close']
        st.plotly_chart(comparison_chart(stock_data), use_container_width=True)
        st.markdown('<div class="yf-section">Returns Comparison</div>', unsafe_allow_html=True)
        returns = []
        for c, prices in stock_data.items():
            ret = round(((prices.iloc[-1]-prices.iloc[0])/prices.iloc[0])*100,2)
            vol = round(prices.pct_change().std()*(252**0.5)*100, 2)
            returns.append({'Company':c,'Return (%)':ret,'Volatility (%)':vol})
        ret_df = pd.DataFrame(returns).sort_values('Return (%)',ascending=False)
        st.dataframe(ret_df, use_container_width=True)
        st.bar_chart(ret_df.set_index('Company')['Return (%)'])

# ── PORTFOLIO PAGE ────────────────────────────────────────────────────────────
elif page == 'Portfolio Tracker':
    st.markdown('<div class="yf-section">Portfolio Tracker</div>', unsafe_allow_html=True)
    port_stocks = st.multiselect('Select Holdings',
        list(COMPANIES.keys()), default=['Nike','Apple','Microsoft','Tesla'])
    if port_stocks:
        st.write('Set your portfolio weights (must add up to 100%)')
        weights = []
        cols_p = st.columns(len(port_stocks))
        for i, stock in enumerate(port_stocks):
            with cols_p[i]:
                w = st.number_input(f'{stock} %', 0, 100,
                    value=round(100//len(port_stocks)), key=f'pw_{stock}')
                weights.append(w)
        total = sum(weights)
        if total == 100:
            port_returns, port_vols = [], []
            details = []
            for stock, w in zip(port_stocks, weights):
                h = fetch_history(COMPANIES[stock], '1y')['Close']
                ret = ((h.iloc[-1]-h.iloc[0])/h.iloc[0])*100
                vol = h.pct_change().std()*(252**0.5)*100
                port_returns.append(ret * w/100)
                port_vols.append(vol * w/100)
                details.append({'Stock':stock,'Weight (%)':w,
                                 'Return (%)':round(ret,2),
                                 'Contribution (%)':round(ret*w/100,2)})
            total_ret = round(sum(port_returns),2)
            total_vol = round(sum(port_vols),2)
            sharpe    = round(total_ret/total_vol,2) if total_vol else 0
            c1,c2,c3 = st.columns(3)
            c1.metric('Portfolio Return (1Y)', f'{total_ret}%')
            c2.metric('Portfolio Volatility',  f'{total_vol}%')
            c3.metric('Sharpe Ratio',          sharpe)
            st.dataframe(pd.DataFrame(details), use_container_width=True)
            st.bar_chart(pd.DataFrame(details).set_index('Stock')['Weight (%)'])
        else:
            st.warning(f'Weights must add to 100%. Currently: {total}%')

# ── PRICE FORECAST PAGE ───────────────────────────────────────────────────────
elif page == 'Price Forecast':
    st.markdown('<div class="yf-section">30-Day Price Forecast (ML)</div>', unsafe_allow_html=True)
    st.caption("Uses Linear Regression on historical price trends. For educational purposes only.")
    import plotly.graph_objects as go
    close = history['Close'].reset_index(drop=True)
    X = np.array(range(len(close))).reshape(-1,1)
    y = close.values
    model = LinearRegression()
    model.fit(X, y)
    future_X = np.array(range(len(close), len(close)+30)).reshape(-1,1)
    forecast = model.predict(future_X)
    fig_f = go.Figure()
    fig_f.add_trace(go.Scatter(x=list(range(len(close))), y=close,
        name='Historical', line=dict(color='#6001d2', width=2)))
    fig_f.add_trace(go.Scatter(x=list(range(len(close), len(close)+30)), y=forecast,
        name='Forecast', line=dict(color='#f59e0b', dash='dash', width=2)))
    fig_f.add_vrect(x0=len(close)-1, x1=len(close)+29,
        fillcolor='#f59e0b', opacity=0.04, line_width=0)
    fig_f.update_layout(height=500, title=f'{selected_ticker} — 30-Day Linear Forecast',
                        **DARK_LAYOUT)
    st.plotly_chart(fig_f, use_container_width=True)
    current   = close.iloc[-1]
    predicted = forecast[-1]
    direction = 'UP ▲' if predicted > current else 'DOWN ▼'
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric('Current Price',    f'${round(current,2)}')
    col_f2.metric('30-Day Forecast',  f'${round(predicted,2)}')
    col_f3.metric('Expected Move',    f'{round(((predicted-current)/current)*100,2)}%')
    st.warning("This is a simple linear model for educational purposes. Not investment advice.")

# ── CORRELATION HEATMAP PAGE ──────────────────────────────────────────────────
elif page == 'Correlation Heatmap':
    st.markdown('<div class="yf-section">Stock Correlation Heatmap</div>', unsafe_allow_html=True)
    st.caption("Values near +1 = move together | near -1 = move opposite | near 0 = no relationship")
    import plotly.graph_objects as go
    corr_stocks = st.multiselect('Select Stocks', list(COMPANIES.keys()),
        default=['Apple','Microsoft','Tesla','JPMorgan','Nike','Amazon'])
    if len(corr_stocks) >= 2:
        with st.spinner('Calculating correlations...'):
            price_data = {}
            for s in corr_stocks:
                h = fetch_history(COMPANIES[s], period)
                price_data[s] = h['Close']
            df_corr = pd.DataFrame(price_data).pct_change().dropna()
            corr_matrix = df_corr.corr()
        fig_c = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns.tolist(),
            y=corr_matrix.index.tolist(),
            colorscale='RdBu', zmid=0, zmin=-1, zmax=1,
            text=corr_matrix.round(2).values,
            texttemplate='%{text}',
            textfont=dict(size=12),
            hoverongaps=False
        ))
        fig_c.update_layout(height=500, title='Return Correlation Matrix', **DARK_LAYOUT)
        st.plotly_chart(fig_c, use_container_width=True)
        st.markdown('<div class="yf-section">Interpretation</div>', unsafe_allow_html=True)
        for i in range(len(corr_stocks)):
            for j in range(i+1, len(corr_stocks)):
                val = round(corr_matrix.iloc[i,j], 2)
                s1, s2 = corr_stocks[i], corr_stocks[j]
                if val > 0.7:
                    st.write(f"**{s1} & {s2}**: Highly correlated ({val}) — move together")
                elif val < -0.3:
                    st.write(f"**{s1} & {s2}**: Negative correlation ({val}) — good for diversification")
    else:
        st.info('Select at least 2 stocks')

# ── MONTE CARLO PAGE ──────────────────────────────────────────────────────────
elif page == 'Monte Carlo':
    st.markdown('<div class="yf-section">Monte Carlo Portfolio Simulation</div>', unsafe_allow_html=True)
    st.caption("Simulates 500 possible portfolio paths over the next 252 trading days (1 year)")
    import plotly.graph_objects as go
    mc_stocks = st.multiselect('Select Portfolio Stocks', list(COMPANIES.keys()),
        default=['Apple','Microsoft','JPMorgan','Nike'])
    invest = st.number_input('Investment Amount ($)', 1000, 1000000, 10000, step=1000)
    simulations = 500
    days = 252
    if mc_stocks and st.button('▶ Run Simulation'):
        with st.spinner('Running 500 simulations...'):
            returns_list = []
            for s in mc_stocks:
                h = fetch_history(COMPANIES[s], '2y')['Close']
                returns_list.append(h.pct_change().dropna())
            df_ret = pd.concat(returns_list, axis=1).dropna()
            df_ret.columns = mc_stocks
            weights = np.array([1/len(mc_stocks)]*len(mc_stocks))
            port_ret = df_ret.dot(weights)
            mu  = port_ret.mean()
            sig = port_ret.std()
            fig_m = go.Figure()
            end_values = []
            for i in range(simulations):
                daily = np.random.normal(mu, sig, days)
                path  = invest * np.cumprod(1 + daily)
                end_values.append(path[-1])
                fig_m.add_trace(go.Scatter(y=path, mode='lines',
                    line=dict(color='rgba(96,1,210,0.05)', width=1), showlegend=False))
            p10 = round(np.percentile(end_values, 10), 2)
            p50 = round(np.percentile(end_values, 50), 2)
            p90 = round(np.percentile(end_values, 90), 2)
            fig_m.update_layout(height=500,
                title=f'Monte Carlo: {simulations} Simulations over {days} Days',
                yaxis_title='Portfolio Value ($)', xaxis_title='Trading Days',
                **DARK_LAYOUT)
            st.plotly_chart(fig_m, use_container_width=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Initial Investment',  f'${invest:,}')
            c2.metric('Best Case (90th %)',  f'${p90:,}')
            c3.metric('Median Outcome',      f'${p50:,}')
            c4.metric('Worst Case (10th %)', f'${p10:,}')
            gain = round(((p50-invest)/invest)*100, 1)
            st.metric('Expected Return (median)', f'{gain}%')
            st.warning("Monte Carlo simulation is for educational purposes only. Not investment advice.")

# ── STOCK SCREENER PAGE ───────────────────────────────────────────────────────
elif page == 'Stock Screener':
    st.markdown('<div class="yf-section">Stock Screener</div>', unsafe_allow_html=True)
    with st.spinner('Loading all stock data...'):
        df_all = fetch_all_stocks()
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        max_pe   = st.slider('Max PE Ratio',        0, 100, 50)
        min_roe  = st.slider('Min ROE (%)',        -50, 100,  0)
    with col_s2:
        min_mktcap = st.slider('Min Market Cap ($B)', 0, 500,   0)
        max_debt   = st.slider('Max Debt/Equity',     0, 500, 300)
    with col_s3:
        min_margin = st.slider('Min Profit Margin (%)', -50, 100, 0)
        min_div    = st.slider('Min Dividend Yield (%)',  0,  10,  0)
    filtered = df_all[
        (df_all['PE Ratio'].between(0, max_pe) | (df_all['PE Ratio'] == 0)) &
        (df_all['ROE (%)'] >= min_roe) &
        (df_all['Market Cap $B'] >= min_mktcap) &
        (df_all['Debt/Equity'] <= max_debt) &
        (df_all['Profit Margin %'] >= min_margin) &
        (df_all['Div Yield (%)'] >= min_div)
    ]
    st.markdown(f'<div class="yf-kpi"><div class="yf-kpi-label">Matching Stocks</div><div class="yf-kpi-value">{len(filtered)}</div></div>',
                unsafe_allow_html=True)
    show_cols = ['Company','Ticker','Price ($)','Change (%)','Market Cap $B',
                 'PE Ratio','ROE (%)','Profit Margin %','Div Yield (%)','Analyst Rating']
    st.dataframe(filtered[show_cols].sort_values('Market Cap $B', ascending=False),
                 use_container_width=True, height=400)
    if len(filtered) > 0:
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button('⬇ Download Screener Results', csv, 'screened_stocks.csv', 'text/csv')

# ── MARKET SENTIMENT PAGE ─────────────────────────────────────────────────────
elif page == 'Market Sentiment':
    st.markdown('<div class="yf-section">Market Sentiment Overview</div>', unsafe_allow_html=True)
    import plotly.graph_objects as go
    with st.spinner('Analyzing sentiment across all stocks...'):
        df_all = fetch_all_stocks()
    gainers     = len(df_all[df_all['Change (%)'] > 0])
    losers      = len(df_all[df_all['Change (%)'] < 0])
    total       = len(df_all)
    bullish_pct = round((gainers/total)*100)
    gauge_color = '#00c878' if bullish_pct >= 60 else '#ff4b4b' if bullish_pct < 40 else '#f59e0b'
    fig_sent = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=bullish_pct,
        domain={'x':[0,1],'y':[0,1]},
        title={'text':'Market Sentiment (% Stocks Up Today)', 'font':{'color':'#aaa'}},
        number={'font':{'color':'#fff','size':48}},
        gauge={
            'axis':{'range':[0,100], 'tickcolor':'#444'},
            'bar':{'color': gauge_color},
            'bgcolor':'#1a1a1a',
            'bordercolor':'#333',
            'steps':[
                {'range':[0,30],  'color':'rgba(255,75,75,0.15)'},
                {'range':[30,60], 'color':'rgba(245,158,11,0.15)'},
                {'range':[60,100],'color':'rgba(0,200,120,0.15)'},
            ],
            'threshold':{'line':{'color':'#fff','width':3},'thickness':0.75,'value':50}
        }
    ))
    fig_sent.update_layout(height=380, paper_bgcolor='#111', font=dict(color='#aaa'))
    st.plotly_chart(fig_sent, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric('Stocks Up Today',   gainers, f'{bullish_pct}%')
    c2.metric('Stocks Down Today', losers,  f'{100-bullish_pct}%')
    label = 'BULLISH 🟢' if bullish_pct > 60 else 'BEARISH 🔴' if bullish_pct < 40 else 'NEUTRAL 🟡'
    c3.metric('Overall Signal', label)
    st.markdown('<hr>', unsafe_allow_html=True)
    if 'Sector' in df_all.columns:
        st.markdo
