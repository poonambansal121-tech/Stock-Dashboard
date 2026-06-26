from textblob import TextBlob

def format_number(val: float, prefix: str = '') -> str:
    """Format large numbers into readable format."""
    if val >= 1e12:
        return f'{prefix}{val/1e12:.2f}T'
    elif val >= 1e9:
        return f'{prefix}{val/1e9:.2f}B'
    elif val >= 1e6:
        return f'{prefix}{val/1e6:.2f}M'
    return f'{prefix}{val:.2f}'

def color_value(val: float) -> str:
    """Return CSS color based on positive/negative value."""
    if isinstance(val, (int, float)):
        c = 'green' if val > 0 else 'red'
        return f'color: {c}; font-weight: bold'
    return ''

def get_sentiment(text: str) -> tuple:
    """Return sentiment label and score for a text."""
    score = TextBlob(text).sentiment.polarity
    if score > 0.1:
        return 'Positive', 'green', score
    elif score < -0.1:
        return 'Negative', 'red', score
    return 'Neutral', 'gray', score
