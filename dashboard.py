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
        'Price Forecast',
        'Correlation Heatmap',
        'Monte Carlo',
        'Stock Screener',
        'Market Sentiment',
        'Market Overview'
    ])
    st.divider()
    mode = st.radio('Pick Stock', ['From List', 'Enter Any Ticker'], horizontal=True)
    if mode == 'Enter Any Ticker':
        custom = st.text_input('Ticker Symbol (e.g. GOOGL, V, META)', '').upper().strip()
        selected_ticker  = custom if custom else 'AAPL'
        selected_company = selected_ticker
    else:
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


# ── PRICE FORECAST PAGE ──
elif page == 'Price Forecast':
    st.markdown('<div class="section-title">30-Day Price Forecast (ML)</div>', unsafe_allow_html=True)
    st.caption("Uses Linear Regression on historical price trends. For educational purposes only.")
    close = history['Close'].reset_index(drop=True)
    X = np.array(range(len(close))).reshape(-1,1)
    y = close.values
    model = LinearRegression()
    model.fit(X, y)
    future_X = np.array(range(len(close), len(close)+30)).reshape(-1,1)
    forecast = model.predict(future_X)
    import plotly.graph_objects as go
    fig_f = go.Figure()
    fig_f.add_trace(go.Scatter(x=list(range(len(close))), y=close,
        name='Historical', line=dict(color='#1B3A6B')))
    fig_f.add_trace(go.Scatter(x=list(range(len(close), len(close)+30)), y=forecast,
        name='Forecast', line=dict(color='#ff8c00', dash='dash')))
    fig_f.add_vrect(x0=len(close)-1, x1=len(close)+29,
        fillcolor='orange', opacity=0.05, line_width=0)
    fig_f.update_layout(height=500, template='plotly_white',
        title=f'{selected_ticker} — 30-Day Linear Forecast')
    st.plotly_chart(fig_f, use_container_width=True)
    current = close.iloc[-1]
    predicted = forecast[-1]
    direction = 'UP' if predicted > current else 'DOWN'
    color = 'positive' if predicted > current else 'negative'
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.metric('Current Price', f'${round(current,2)}')
    col_f2.metric('30-Day Forecast', f'${round(predicted,2)}')
    col_f3.metric('Expected Move', f'{round(((predicted-current)/current)*100,2)}%')
    st.warning("This is a simple linear model for educational purposes. Not investment advice.")


# ── CORRELATION HEATMAP PAGE ──
elif page == 'Correlation Heatmap':
    st.markdown('<div class="section-title">Stock Correlation Heatmap</div>', unsafe_allow_html=True)
    st.caption("Values near +1 = move together | near -1 = move opposite | near 0 = no relationship")
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
        import plotly.graph_objects as go
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
        fig_c.update_layout(height=500, template='plotly_white',
            title='Return Correlation Matrix')
        st.plotly_chart(fig_c, use_container_width=True)
        st.subheader('What this means')
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


# ── MONTE CARLO PAGE ──
elif page == 'Monte Carlo':
    st.markdown('<div class="section-title">Monte Carlo Portfolio Simulation</div>', unsafe_allow_html=True)
    st.caption("Simulates 500 possible portfolio paths over the next 252 trading days (1 year)")
    mc_stocks = st.multiselect('Select Portfolio Stocks', list(COMPANIES.keys()),
        default=['Apple','Microsoft','JPMorgan','Nike'])
    invest = st.number_input('Investment Amount ($)', 1000, 1000000, 10000, step=1000)
    simulations = 500
    days = 252
    if mc_stocks and st.button('Run Simulation'):
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
            import plotly.graph_objects as go
            fig_m = go.Figure()
            end_values = []
            for i in range(simulations):
                daily = np.random.normal(mu, sig, days)
                path  = invest * np.cumprod(1 + daily)
                end_values.append(path[-1])
                color = 'rgba(27,58,107,0.04)'
                fig_m.add_trace(go.Scatter(y=path, mode='lines',
                    line=dict(color=color, width=1), showlegend=False))
            p10 = round(np.percentile(end_values, 10), 2)
            p50 = round(np.percentile(end_values, 50), 2)
            p90 = round(np.percentile(end_values, 90), 2)
            fig_m.update_layout(height=500, template='plotly_white',
                title=f'Monte Carlo: {simulations} Simulations over {days} Days',
                yaxis_title='Portfolio Value ($)', xaxis_title='Trading Days')
            st.plotly_chart(fig_m, use_container_width=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Initial Investment', f'${invest:,}')
            c2.metric('Best Case (90th %)', f'${p90:,}')
            c3.metric('Median Outcome', f'${p50:,}')
            c4.metric('Worst Case (10th %)', f'${p10:,}')
            gain = round(((p50-invest)/invest)*100, 1)
            st.metric('Expected Return (median)', f'{gain}%')
            st.warning("Monte Carlo simulation is for educational purposes only. Not investment advice.")


# ── STOCK SCREENER PAGE ──
elif page == 'Stock Screener':
    st.markdown('<div class="section-title">Stock Screener</div>', unsafe_allow_html=True)
    with st.spinner('Loading all stock data...'):
        df_all = fetch_all_stocks()
    st.subheader('Filter Stocks')
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        max_pe = st.slider('Max PE Ratio', 0, 100, 50)
        min_roe = st.slider('Min ROE (%)', -50, 100, 0)
    with col_s2:
        min_mktcap = st.slider('Min Market Cap ($B)', 0, 500, 0)
        max_debt = st.slider('Max Debt/Equity', 0, 500, 300)
    with col_s3:
        min_margin = st.slider('Min Profit Margin (%)', -50, 100, 0)
        min_div = st.slider('Min Dividend Yield (%)', 0, 10, 0)
    filtered = df_all[
        (df_all['PE Ratio'].between(0, max_pe) | (df_all['PE Ratio'] == 0)) &
        (df_all['ROE (%)'] >= min_roe) &
        (df_all['Market Cap $B'] >= min_mktcap) &
        (df_all['Debt/Equity'] <= max_debt) &
        (df_all['Profit Margin %'] >= min_margin) &
        (df_all['Div Yield (%)'] >= min_div)
    ]
    st.markdown(f"**{len(filtered)} stocks match your criteria**")
    show_cols = ['Company','Ticker','Price ($)','Change (%)','Market Cap $B',
                 'PE Ratio','ROE (%)','Profit Margin %','Div Yield (%)','Analyst Rating']
    st.dataframe(filtered[show_cols].sort_values('Market Cap $B', ascending=False),
                 use_container_width=True, height=400)
    if len(filtered) > 0:
        csv = filtered.to_csv(index=False).encode('utf-8')
        st.download_button('Download Screener Results', csv, 'screened_stocks.csv', 'text/csv')

# ── MARKET SENTIMENT PAGE ──
elif page == 'Market Sentiment':
    st.markdown('<div class="section-title">Market Sentiment Overview</div>', unsafe_allow_html=True)
    with st.spinner('Analyzing sentiment across all stocks...'):
        df_all = fetch_all_stocks()
    gainers = len(df_all[df_all['Change (%)'] > 0])
    losers  = len(df_all[df_all['Change (%)'] < 0])
    total   = len(df_all)
    bullish_pct = round((gainers/total)*100)
    import plotly.graph_objects as go
    fig_sent = go.Figure(go.Indicator(
        mode='gauge+number+delta',
        value=bullish_pct,
        domain={'x':[0,1],'y':[0,1]},
        title={'text':'Market Sentiment (% Stocks Up Today)'},
        gauge={
            'axis':{'range':[0,100]},
            'bar':{'color':'#1B3A6B'},
            'steps':[
                {'range':[0,30],  'color':'#ff4b4b'},
                {'range':[30,60], 'color':'#ffd700'},
                {'range':[60,100],'color':'#00d4aa'},
            ],
            'threshold':{'line':{'color':'black','width':4},'thickness':0.75,'value':50}
        }
    ))
    fig_sent.update_layout(height=400, template='plotly_white')
    st.plotly_chart(fig_sent, use_container_width=True)
    c1, c2, c3 = st.columns(3)
    c1.metric('Stocks Up Today',   gainers, f'{bullish_pct}%')
    c2.metric('Stocks Down Today', losers,  f'{100-bullish_pct}%')
    label = 'BULLISH' if bullish_pct > 60 else 'BEARISH' if bullish_pct < 40 else 'NEUTRAL'
    c3.metric('Overall Signal', label)
    st.divider()
    st.subheader('Sentiment by Sector')
    if 'Sector' in df_all.columns:
        sector_sent = df_all.groupby('Sector')['Change (%)'].mean().sort_values(ascending=False)
        st.bar_chart(sector_sent)


# ── MONTE CARLO PAGE ──
elif page == 'Monte Carlo':
    st.markdown('<div class="section-title">Monte Carlo Portfolio Simulation</div>', unsafe_allow_html=True)
    st.caption("Simulates 500 possible portfolio paths over the next 252 trading days (1 year)")
    mc_stocks = st.multiselect('Select Portfolio Stocks', list(COMPANIES.keys()),
        default=['Apple','Microsoft','JPMorgan','Nike'])
    invest = st.number_input('Investment Amount ($)', 1000, 1000000, 10000, step=1000)
    simulations = 500
    days = 252
    if mc_stocks and st.button('Run Simulation'):
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
            import plotly.graph_objects as go
            fig_m = go.Figure()
            end_values = []
            for i in range(simulations):
                daily = np.random.normal(mu, sig, days)
                path  = invest * np.cumprod(1 + daily)
                end_values.append(path[-1])
                color = 'rgba(27,58,107,0.04)'
                fig_m.add_trace(go.Scatter(y=path, mode='lines',
                    line=dict(color=color, width=1), showlegend=False))
            p10 = round(np.percentile(end_values, 10), 2)
            p50 = round(np.percentile(end_values, 50), 2)
            p90 = round(np.percentile(end_values, 90), 2)
            fig_m.update_layout(height=500, template='plotly_white',
                title=f'Monte Carlo: {simulations} Simulations over {days} Days',
                yaxis_title='Portfolio Value ($)', xaxis_title='Trading Days')
            st.plotly_chart(fig_m, use_container_width=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Initial Investment', f'${invest:,}')
            c2.metric('Best Case (90th %)', f'${p90:,}')
            c3.metric('Median Outcome', f'${p50:,}')
            c4.metric('Worst Case (10th %)', f'${p10:,}')
            gain = round(((p50-invest)/invest)*100, 1)
            st.metric('Expected Return (median)', f'{gain}%')
            st.warning("Monte Carlo simulation is for educational purposes only. Not investment advice.")

# ── FOOTER ──
st.markdown('<br><hr>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#888">'
            'Built by <b>Poonam Dhanuka</b> | DePaul MS Finance 2027 | '
            'Data: Yahoo Finance | Educational purposes only</div>',
            unsafe_allow_html=True)
