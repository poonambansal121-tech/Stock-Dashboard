import yfinance as yf
import pandas as pd
import streamlit as st
import time
import random
from curl_cffi import requests as curl_requests
from config import COMPANIES, CACHE_TTL

# ── SHARED SESSION ─────────────────────────────────────────────────────────
# yfinance authenticates by fetching a cookie + "crumb" from Yahoo before every
# request. If you create a fresh yf.Ticker() (with no session) for every call,
# yfinance re-fetches that cookie/crumb EVERY TIME. On Streamlit Cloud, many
# apps share the same outbound IP range, so rapid crumb re-fetching is exactly
# what trips Yahoo's rate limiter (YFRateLimitError).
#
# Using one curl_cffi session (with a browser "impersonate" fingerprint, which
# yfinance's own docs now recommend for cloud/server deployments) for the
# whole process means the cookie + crumb are fetched once and reused across
# every ticker and every page, drastically cutting the number of auth calls.
_session = curl_requests.Session(impersonate="chrome")


def _get_ticker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker, session=_session)


def _with_retry(fn, retries=3, base_delay=6):
    """Retry with longer backoff + jitter. Yahoo's rate-limit window tends to
    be tens of seconds, so short/immediate retries just get limited again."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return fn()
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(base_delay * attempt + random.uniform(0, 2))
    raise last_err


@st.cache_data(ttl=CACHE_TTL)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    """Fetch historical OHLCV data."""
    df = _with_retry(lambda: _get_ticker(ticker).history(period=period))
    df.index = df.index.tz_localize(None)
    return df


@st.cache_data(ttl=CACHE_TTL)
def fetch_info(ticker: str) -> dict:
    """Fetch company info and fundamentals."""
    return _with_retry(lambda: _get_ticker(ticker).info)


@st.cache_data(ttl=CACHE_TTL)
def fetch_news(ticker: str) -> list:
    """Fetch latest news for a ticker."""
    return _with_retry(lambda: _get_ticker(ticker).news[:10])


# fetch_all_stocks hits every company back to back, so it's the single biggest
# source of rate-limit risk. Cache it for at least 30 minutes regardless of
# the configured CACHE_TTL, so this expensive loop runs as rarely as possible.
@st.cache_data(ttl=max(CACHE_TTL, 1800))
def fetch_all_stocks() -> pd.DataFrame:
    """Fetch summary data for all companies."""
    data = []
    for name, ticker in COMPANIES.items():
        try:
            info = _with_retry(lambda t=ticker: _get_ticker(t).info, retries=2, base_delay=4)
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
            # Slower, jittered pacing between tickers so this loop doesn't read
            # as a burst of automated requests.
            time.sleep(1.5 + random.uniform(0, 1.5))
        except Exception:
            continue
    return pd.DataFrame(data)
