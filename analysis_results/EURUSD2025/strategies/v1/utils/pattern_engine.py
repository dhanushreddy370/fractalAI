import pandas as pd
from datetime import time
import numpy as np

"""
Pattern Engine for EUR/USD Momentum Scalper - Pure OHLC Version
"""

# Define session times in UTC (00:00-24:00 UTC as specified)
SESSION_TIMES = {
    "Session": (time(0, 0), time(23, 59, 59))  # Full 24-hour session
}

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

def get_session_high_low(df_m1, session_name, current_day):
    """
    Calculates the high and low of a specific trading session for a given day.
    """
    if df_m1 is None or df_m1.empty:
        return None, None
    if not df_m1.index.is_monotonic_increasing:
        df_m1 = df_m1.sort_index()

    start_time, end_time = SESSION_TIMES.get(session_name, (None, None))
    if start_time is None:
        return None, None

    day_str = current_day.strftime('%Y-%m-%d')
    mask = ((df_m1.index >= f"{day_str} {start_time}") & (df_m1.index <= f"{day_str} {end_time}"))

    session_df = df_m1.loc[mask]
    if not session_df.empty:
        return session_df['high'].max(), session_df['low'].min()
    return None, None

def get_key_levels(all_data, current_time):
    """
    Gathers all relevant key levels at a specific point in time.
    """
    levels = {}
    
    # Get weekly levels (from Friday close)
    if 'W1' in all_data and not all_data['W1'].empty:
        prev_weekly_bar = get_previous_bar(all_data['W1'], current_time)
        if prev_weekly_bar is not None:
            levels['prev_W1_high'] = prev_weekly_bar['high']
            levels['prev_W1_low'] = prev_weekly_bar['low']
    
    # Get daily levels
    if 'D1' in all_data and not all_data['D1'].empty:
        prev_daily_bar = get_previous_bar(all_data['D1'], current_time)
        if prev_daily_bar is not None:
            levels['prev_D1_high'] = prev_daily_bar['high']
            levels['prev_D1_low'] = prev_daily_bar['low']
    
    # Get H4 levels
    if 'H4' in all_data and not all_data['H4'].empty:
        prev_h4_bar = get_previous_bar(all_data['H4'], current_time)
        if prev_h4_bar is not None:
            levels['prev_H4_high'] = prev_h4_bar['high']
            levels['prev_H4_low'] = prev_h4_bar['low']
    
    # Get H1 levels
    if 'H1' in all_data and not all_data['H1'].empty:
        prev_h1_bar = get_previous_bar(all_data['H1'], current_time)
        if prev_h1_bar is not None:
            levels['prev_H1_high'] = prev_h1_bar['high']
            levels['prev_H1_low'] = prev_h1_bar['low']
    
    # Get session levels (00:00-24:00 UTC)
    if 'M1' in all_data and not all_data['M1'].empty:
        current_day = current_time.normalize()
        for session in SESSION_TIMES.keys():
            sh, sl = get_session_high_low(all_data['M1'], session, current_day)
            if sh is not None: levels[f'{session}_high'] = sh
            if sl is not None: levels[f'{session}_low'] = sl
    
    return levels

def is_within_percentage(price, level, percentage):
    """
    Check if price is within a certain percentage of a level.
    """
    if level == 0:
        return False
    return abs(price - level) / level <= percentage

def is_breached(close_price, level, direction):
    """
    Check if a level is breached by a close price.
    """
    if direction == 'above':
        return close_price > level * 1.0001  # Breached by at least 0.01%
    else:
        return close_price < level * 0.9999  # Breached by at least 0.01%

def is_sweep(high_price, low_price, level, level_type):
    """
    Check if price swept a level.
    """
    if level_type == 'high':
        return high_price > level * 1.001 and low_price < level  # Swept by 0.1% and closed back
    else:
        return low_price < level * 0.999 and high_price > level  # Swept by 0.1% and closed back