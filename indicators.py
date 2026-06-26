import pandas as pd

def compute_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(period).mean()

def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period).mean()

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta    = series.diff()
    gain     = delta.clip(lower=0)
    loss     = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def compute_macd(series: pd.Series) -> tuple:
    """MACD and Signal line."""
    ema12  = series.ewm(span=12).mean()
    ema26  = series.ewm(span=26).mean()
    macd   = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist   = macd - signal
    return macd, signal, hist

def compute_bollinger(series: pd.Series, period: int = 20) -> tuple:
    """Bollinger Bands: upper, middle, lower."""
    sma     = series.rolling(period).mean()
    std_dev = series.rolling(period).std()
    upper   = sma + (std_dev * 2)
    lower   = sma - (std_dev * 2)
    return upper, sma, lower
