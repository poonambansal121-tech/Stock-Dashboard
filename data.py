import yfinance as yf
import pandas as pd
import streamlit as st
import time
from config import COMPANIES, CACHE_TTL

@st.cache_data(ttl=CACHE_TTL)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    """Fetch historical OHLCV data."""
    df = yf.Ticker(ticker).history(period=period)
    df.index = df.index.tz_localize(None)
    return df

@st.cache_data(ttl=CACHE_TTL)
def fetch_info(ticker: str) -> dict:
    """Fetch company info and fundamentals."""
    return yf.Ticker(ticker).info

@st.cache_data(ttl=CACHE_TTL)
def fetch_news(ticker: str) -> list:
    """Fetch latest news for a ticker."""
    return yf.Ticker(ticker).news[:10]

@st.cache_data(ttl=CACHE_TTL)
def fetch_all_stocks() -> pd.DataFrame:
    """Fetch summary data for all companies."""
    data = []
    for name, ticker in COMPANIES.items():
        try:
            info  = yf.Ticker(ticker).info
            price = info.get('currentPrice', 0)
            prev  = info.get('previousClose', price)
            chg   = round(price - prev, 2)
            pct   = round((chg/prev)*100, 2) if prev else 0
            data.append({
                'Company':          name,
                'Ticker':           ticker,
                'Price ($)':        price,
                'Change (%)':       pct,
                'Market Cap $B':    round(info.get('marketCap',0)/1e9, 2),
                'Revenue $B':       round(info.get('totalRevenue',0)/1e9, 2),
                'PE Ratio':         round(info.get('trailingPE',0), 2),
                'Forward PE':       round(info.get('forwardPE',0), 2),
                'PB Ratio':         round(info.get('priceToBook',0), 2),
                'EPS ($)':          round(info.get('trailingEps',0), 2),
                'Beta':             round(info.get('beta',0), 2),
                'ROE (%)':          round(info.get('returnOnEquity',0)*100, 2),
                'ROA (%)':          round(info.get('returnOnAssets',0)*100, 2),
                'Profit Margin %':  round(info.get('profitMargins',0)*100, 2),
                'Gross Margin %':   round(info.get('grossMargins',0)*100, 2),
                'Debt/Equity':      round(info.get('debtToEquity',0), 2),
                'Current Ratio':    round(info.get('currentRatio',0), 2),
                'Quick Ratio':      round(info.get('quickRatio',0), 2),
                'Div Yield (%)':    round(info.get('dividendYield',0)*100, 2),
                '52W High ($)':     info.get('fiftyTwoWeekHigh',0),
                '52W Low ($)':      info.get('fiftyTwoWeekLow',0),
                'Target Price ($)': round(info.get('targetMeanPrice',0), 2),
                'Analyst Rating':   info.get('recommendationKey','N/A').upper(),
                'Employees':        info.get('fullTimeEmployees',0),
                'Sector':           info.get('sector','N/A'),
                'Industry':         info.get('industry','N/A'),
                'HQ':               info.get('city','')+', '+info.get('state',''),
                'Website':          info.get('website','N/A'),
                'Logo':             info.get('logo_url',''),
                'Description':      info.get('longBusinessSummary','N/A'),
            })
            time.sleep(0.5)
        except:
            pass
    return pd.DataFrame(data)
