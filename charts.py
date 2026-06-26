import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from indicators import compute_sma, compute_ema, compute_rsi, compute_macd, compute_bollinger

TEMPLATE = 'plotly_white'

def candlestick_chart(history: pd.DataFrame, show_sma20=True,
                       show_sma50=True, show_sma200=False,
                       show_ema=False, show_bb=False,
                       show_volume=True) -> go.Figure:
    """Create candlestick chart with optional overlays."""
    rows = 2 if show_volume else 1
    heights = [0.7, 0.3] if show_volume else [1]
    fig = make_subplots(rows=rows, cols=1,
                        shared_xaxes=True, row_heights=heights)
    fig.add_trace(go.Candlestick(
        x=history.index, open=history['Open'],
        high=history['High'], low=history['Low'],
        close=history['Close'], name='OHLC',
        increasing_line_color='#00d4aa',
        decreasing_line_color='#ff4b4b'
    ), row=1, col=1)
    if show_sma20:
        fig.add_trace(go.Scatter(x=history.index,
            y=compute_sma(history['Close'],20),
            name='SMA20', line=dict(color='#1B3A6B',width=1)), row=1, col=1)
    if show_sma50:
        fig.add_trace(go.Scatter(x=history.index,
            y=compute_sma(history['Close'],50),
            name='SMA50', line=dict(color='#ff8c00',width=1)), row=1, col=1)
    if show_sma200:
        fig.add_trace(go.Scatter(x=history.index,
            y=compute_sma(history['Close'],200),
            name='SMA200', line=dict(color='#9370db',width=1)), row=1, col=1)
    if show_ema:
        fig.add_trace(go.Scatter(x=history.index,
            y=compute_ema(history['Close'],20),
            name='EMA20', line=dict(color='#00bfff',width=1,dash='dash')), row=1, col=1)
    if show_bb:
        upper, mid, lower = compute_bollinger(history['Close'])
        fig.add_trace(go.Scatter(x=history.index, y=upper,
            name='BB Upper', line=dict(color='gray',width=1,dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=history.index, y=lower,
            name='BB Lower', line=dict(color='gray',width=1,dash='dot'),
            fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
    if show_volume:
        colors = ['#00d4aa' if c >= o else '#ff4b4b'
                  for c,o in zip(history['Close'], history['Open'])]
        fig.add_trace(go.Bar(x=history.index, y=history['Volume'],
            name='Volume', marker_color=colors), row=2, col=1)
    fig.update_layout(height=600, template=TEMPLATE,
                      xaxis_rangeslider_visible=False,
                      legend=dict(orientation='h', y=1.02))
    return fig

def indicator_chart(history: pd.DataFrame,
                    show_rsi=True, show_macd=True) -> go.Figure:
    """Create technical indicator chart."""
    rows = 1 + show_rsi + show_macd
    titles = ['Price'] + (['RSI'] if show_rsi else []) + (['MACD'] if show_macd else [])
    fig = make_subplots(rows=rows, cols=1,
                        shared_xaxes=True, subplot_titles=titles)
    fig.add_trace(go.Scatter(x=history.index, y=history['Close'],
        name='Price', line=dict(color='#1B3A6B')), row=1, col=1)
    row = 2
    if show_rsi:
        rsi = compute_rsi(history['Close'])
        fig.add_trace(go.Scatter(x=history.index, y=rsi,
            name='RSI', line=dict(color='#ff8c00')), row=row, col=1)
        fig.add_hline(y=70, line_color='red',   line_dash='dash', row=row, col=1)
        fig.add_hline(y=30, line_color='green', line_dash='dash', row=row, col=1)
        row += 1
    if show_macd:
        macd, signal, hist = compute_macd(history['Close'])
        fig.add_trace(go.Scatter(x=history.index, y=macd,
            name='MACD', line=dict(color='#1B3A6B')), row=row, col=1)
        fig.add_trace(go.Scatter(x=history.index, y=signal,
            name='Signal', line=dict(color='#ff4b4b')), row=row, col=1)
        fig.add_trace(go.Bar(x=history.index, y=hist,
            name='Histogram', marker_color='#00d4aa'), row=row, col=1)
    fig.update_layout(height=700, template=TEMPLATE)
    return fig

def comparison_chart(stock_data: dict) -> go.Figure:
    """Normalized price comparison chart."""
    fig = go.Figure()
    colors = ['#1B3A6B','#00d4aa','#ff4b4b','#ff8c00','#9370db']
    for i,(name,prices) in enumerate(stock_data.items()):
        norm = (prices / prices.iloc[0]) * 100
        fig.add_trace(go.Scatter(x=norm.index, y=norm,
            name=name, line=dict(color=colors[i % len(colors)])))
    fig.update_layout(title='Normalized Price (Base=100)',
                      height=500, template=TEMPLATE,
                      legend=dict(orientation='h', y=1.02))
    return fig
