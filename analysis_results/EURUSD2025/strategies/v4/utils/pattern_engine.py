import pandas as pd

def is_within_percentage(price1, price2, percentage):
    """Check if two prices are within a certain percentage of each other"""
    if price1 == 0 or price2 == 0:
        return False
    return abs(price1 - price2) / price2 <= percentage / 100

def get_previous_bar(df, current_time):
    """
    Gets the most recent bar from a dataframe that closed *before* the current time.
    """
    if df is None or df.empty:
        return None
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
    previous_bars = df[df.index < current_time]
    return previous_bars.iloc[-1] if not previous_bars.empty else None

def calculate_pivot_points(high, low, close):
    """Calculate basic pivot points (support/resistance)"""
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    return {'pivot': pivot, 'r1': r1, 's1': s1}

def detect_price_cluster(levels, current_price, tolerance=0.001):
    """Detect if multiple key levels are clustered around current price"""
    cluster_levels = []
    for level_name, level_price in levels.items():
        if level_price is not None and abs(current_price - level_price) / current_price <= tolerance:
            cluster_levels.append((level_name, level_price))
    return cluster_levels if len(cluster_levels) >= 2 else None

def get_candle_body_size(candle):
    """Get the absolute size of the candle body"""
    return abs(candle['close'] - candle['open'])

def get_candle_range(candle):
    """Get the total range of the candle"""
    return candle['high'] - candle['low']

def is_strong_breakout_candle(candle, breakout_direction):
    """Check if candle shows strong breakout characteristics"""
    body_size = get_candle_body_size(candle)
    total_range = get_candle_range(candle)
    
    if total_range == 0:
        return False
    
    body_ratio = body_size / total_range
    
    if breakout_direction == 'bullish':
        return (candle['close'] > candle['open'] and 
                body_ratio > 0.7 and 
                candle['close'] > candle['high'] * 0.9)
    else:  # bearish
        return (candle['close'] < candle['open'] and 
                body_ratio > 0.7 and 
                candle['close'] < candle['low'] * 1.1)