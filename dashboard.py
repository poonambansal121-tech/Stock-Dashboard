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

st.markdown('''
<style>
    .hero-title { font-size: 2.5rem; font-weight: 800; color: #1B3A6B; }
    .hero-sub { font-size: 1rem; color: #555; margin-bottom: 1rem; }
    .kpi-box { background:#f0f4ff; border-radius:12px; padding:16px;
               border-left:4px solid #1B3A6B; margin-bottom:8px; }
    .section-title { color:#1B3A6B; font-size:1.4rem; font-weight:700; }
    .news-card { background:#f8f9fa; border-radius:10px; padding:14px;
                 margin-bottom:10px; border:1px solid #e0e0e0; }
    .positive { color: #00a86b; font-weight: bold; }
    .negative { color: #ff4b4b; font-weight: bold; }
</style>
''', unsafe_allow_html=True)

# ── SIDEBAR ──
with st.sidebar:
    st.markdown('## Stock Dashboard')
    st.markdown('*Built by Poonam Dhanuka*')
    st.markdown('*DePaul MS Finance 2027*')
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
        'Market Overview'
    ])
    st.divider()
    selected_company = st.selectbox('Select Company', list(COMPANIES.keys()))
    selected_ticker  = COMPANIES[selected_company]
    period = st.select_slider('Time Period',
        options=['1mo','3mo','6mo','1y','2y','5y'], value='1y')
    st.divider()
    st.caption('Data: Yahoo Finance')
    st.caption(now.strftime('%b %d, %Y %I:%M %p') + ' CST')

# ── LOAD DATA ──
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

# ── HERO HEADER ──
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    logo = info.get('logo_url','')
    if logo:
        st.image(logo, width=60)
    st.markdown(f'<div class="hero-title">{selected_company} ({selected_ticker})</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">{info.get("sector","")} | {info.get("industry","")} | {info.get("city","")}, {info.get("state","")}</div>',
                unsafe_allow_html=True)
with col_h2:
    color = 'positive' if pct >= 0 else 'negative'
    arrow = 'UP' if pct >= 0 else 'DOWN'
    st.markdown(f'<div style="text-align:right"><span style="font-size:2rem;font-weight:800">${price}</span><br>'
                f'<span class="{color}">{arrow} {abs(pct)}%</span></div>',
                unsafe_allow_html=True)
st.divider()

# ── OVERVIEW PAGE ──
if page == 'Overview':
    st.markdown('<div class="section-title">Market Snapshot</div>', unsafe_allow_html=True)
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric('Price',        f'${price}',   f'{pct}%')
    c2.metric('Market Cap',   format_number(mktcap,'$'))
    c3.metric('52W High',     f'${high52}')
    c4.metric('52W Low',      f'${low52}')
    c5.metric('Target Price', f'${target}')
    c6.metric('Analyst',      rating)
    st.divider()
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown('<div class="section-title">Price Chart</div>', unsafe_allow_html=True)
        fig = candlestick_chart(history)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown('<div class="section-title">Key Metrics</div>', unsafe_allow_html=True)
        metrics = {
            'PE Ratio':      pe,
            'Beta':          beta,
            'Div Yield':     f'{div}%',
            'EPS':           f'${info.get("trailingEps",0)}',
            'Revenue':       format_number(info.get('totalRevenue',0),'$'),
            'Profit Margin': f'{round(info.get("profitMargins",0)*100,2)}%',
            'ROE':           f'{round(info.get("returnOnEquity",0)*100,2)}%',
            'Debt/Equity':   round(info.get('debtToEquity',0),2),
        }
        for k,v in metrics.items():
            st.markdown(f'<div class="kpi-box"><b>{k}</b>: {v}</div>',
                        unsafe_allow_html=True)
    csv = history.to_csv().encode('utf-8')
    st.download_button('Download Price Data as CSV',
                       csv, f'{selected_ticker}_prices.csv', 'text/csv')

# ── HISTORICAL PRICE PAGE ──
elif page == 'Historical Price':
    st.markdown('<div class="section-title">Historical Price Analysis</div>',
                unsafe_allow_html=True)
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
    st.subheader('Price Statistics')
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric('Average Price', f'${round(history["Close"].mean(),2)}')
    col_s2.metric('Highest Price', f'${round(history["Close"].max(),2)}')
    col_s3.metric('Lowest Price',  f'${round(history["Close"].min(),2)}')
    col_s4.metric('Volatility',    f'{round(history["Close"].pct_change().std()*100,2)}%')
    csv = history.to_csv().encode('utf-8')
    st.download_button('Download Data as CSV',
                       csv, f'{selected_ticker}_history.csv', 'text/csv')

# ── TECHNICAL INDICATORS PAGE ──
elif page == 'Technical Indicators':
    st.markdown('<div class="section-title">Technical Indicators</div>',
                unsafe_allow_html=True)
    col_t1, col_t2 = st.columns(2)
    with col_t1: show_rsi  = st.checkbox('RSI (14)',  True)
    with col_t2: show_macd = st.checkbox('MACD',      True)
    fig = indicator_chart(history, show_rsi, show_macd)
    st.plotly_chart(fig, use_container_width=True)
    st.caption('RSI > 70 = Overbought | RSI < 30 = Oversold | MACD cross = Buy/Sell signal')

# ── FINANCIAL METRICS PAGE ──
elif page == 'Financial Metrics':
    st.markdown('<div class="section-title">Financial Metrics</div>',
                unsafe_allow_html=True)
    with st.spinner('Loading all company data...'):
        df_all = fetch_all_stocks()
    t1,t2,t3 = st.tabs(['Valuation','Profitability','Financial Health'])
    with t1:
        val_df = df_all[['Company','PE Ratio','Forward PE','PB Ratio','EPS ($)','Target Price ($)','Analyst Rating']]
        st.dataframe(val_df, use_container_width=True, height=400)
        st.caption('PE=Price/Earnings | PB=Price/Book | Forward PE uses estimated future earnings')
    with t2:
        prof_df = df_all[['Company','Revenue $B','Profit Margin %','Gross Margin %','ROE (%)','ROA (%)']]
        def color_df(val):
            return color_value(val)
        st.dataframe(prof_df.style.map(color_df,
            subset=['Profit Margin %','Gross Margin %','ROE (%)','ROA (%)']),
            use_container_width=True, height=400)
    with t3:
        health_df = df_all[['Company','Debt/Equity','Current Ratio','Quick Ratio','Beta','Div Yield (%)']]
        st.dataframe(health_df, use_container_width=True, height=400)
        st.caption('Current Ratio > 1 = Healthy | Beta > 1 = More volatile than market')
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button('Download All Metrics as CSV',
                       csv, 'all_stocks.csv', 'text/csv')

# ── COMPANY INFO PAGE ──
elif page == 'Company Info':
    st.markdown('<div class="section-title">Company Information</div>',
                unsafe_allow_html=True)
    logo = info.get('logo_url','')
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
    st.divider()
    st.markdown('**About the Company**')
    st.write(info.get('longBusinessSummary','N/A'))

# ── NEWS PAGE ──
elif page == 'Latest News':
    st.markdown('<div class="section-title">Latest News & Sentiment</div>',
                unsafe_allow_html=True)
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
            st.markdown('<div class="news-card">', unsafe_allow_html=True)
            col_n1, col_n2 = st.columns([4,1])
            with col_n1:
                st.markdown(f'**[{title}]({link})**')
                if summary:
                    st.write(summary[:200]+'...')
                st.caption(pub)
            with col_n2:
                st.markdown(f'<span style="color:{color};font-weight:bold">{label}</span>',
                            unsafe_allow_html=True)
                st.write(f'Score: {round(score,2)}')
            st.markdown('</div>', unsafe_allow_html=True)
            st.divider()
        avg = sum(scores)/len(scores) if scores else 0
        overall = 'Positive' if avg > 0.1 else 'Negative' if avg < -0.1 else 'Neutral'
        st.metric('Overall Sentiment', overall, f'Score: {round(avg,3)}')
    except:
        st.warning('News not available right now. Please try again later.')

# ── COMPARISON PAGE ──
elif page == 'Stock Comparison':
    st.markdown('<div class="section-title">Stock Comparison</div>',
                unsafe_allow_html=True)
    selected_comps = st.multiselect('Select Companies',
        list(COMPANIES.keys()), default=['Nike','Apple','Microsoft'])
    if selected_comps:
        stock_data = {}
        for c in selected_comps:
            h = fetch_history(COMPANIES[c], period)
            stock_data[c] = h['Close']
        st.plotly_chart(comparison_chart(stock_data), use_container_width=True)
        st.subheader('Returns Comparison')
        returns = []
        for c, prices in stock_data.items():
            ret = round(((prices.iloc[-1]-prices.iloc[0])/prices.iloc[0])*100,2)
            vol = round(prices.pct_change().std()*(252**0.5)*100, 2)
            returns.append({'Company':c,'Return (%)':ret,'Volatility (%)':vol})
        ret_df = pd.DataFrame(returns).sort_values('Return (%)',ascending=False)
        st.dataframe(ret_df, use_container_width=True)
        st.bar_chart(ret_df.set_index('Company')['Return (%)'])

# ── PORTFOLIO PAGE ──
elif page == 'Portfolio Tracker':
    st.markdown('<div class="section-title">Portfolio Tracker</div>',
                unsafe_allow_html=True)
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

# ── MARKET OVERVIEW PAGE ──
elif page == 'Market Overview':
    st.markdown('<div class="section-title">Market Overview</div>',
                unsafe_allow_html=True)
    with st.spinner('Loading market data...'):
        df_all = fetch_all_stocks()
    col_g, col_l = st.columns(2)
    with col_g:
        st.subheader('Top Gainers')
        for _,row in df_all.nlargest(5,'Change (%)').iterrows():
            st.metric(row['Company'], f"${row['Price ($)']}", f"+{row['Change (%)']}%")
    with col_l:
        st.subheader('Top Losers')
        for _,row in df_all.nsmallest(5,'Change (%)').iterrows():
            st.metric(row['Company'], f"${row['Price ($)']}", f"{row['Change (%)']}%")
    st.divider()
    st.subheader('All Companies')
    overview = df_all[['Company','Ticker','Price ($)','Change (%)','Market Cap $B','PE Ratio','Analyst Rating']]
    st.dataframe(overview.style.map(color_value, subset=['Change (%)']),
                 use_container_width=True, height=400)
    csv = df_all.to_csv(index=False).encode('utf-8')
    st.download_button('Download as CSV', csv, 'market_overview.csv', 'text/csv')

# ── FOOTER ──
st.markdown('<br><hr>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#888">'
            'Built by <b>Poonam Dhanuka</b> | DePaul MS Finance 2027 | '
            'Data: Yahoo Finance | Educational purposes only</div>',
            unsafe_allow_html=True)
