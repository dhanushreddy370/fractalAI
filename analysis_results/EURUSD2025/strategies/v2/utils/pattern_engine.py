import pandas as pd
from datetime import time

def is_within_percentage(price1, price2, percentage):
    """Check if two prices are within a certain percentage of each other"""
    return abs(price1 - price2) / price2 <= percentage

def get_session_high_low(df_m1, session_name, current_day):
    """
    Calculates the high and low of a specific trading session for a given day.
    """
    if df_m1 is None or df_m1.empty:
        return None, None
    if not df_m1.index.is_monotonic_increasing:
        df_m1 = df_m1.sort_index()

    # Define session times in UTC (00:00-24:00)
    SESSION_TIMES = {
        "Asia": (time(20, 0), time(5, 0)),
        "London": (time(3, 0), time(12, 0)),
        "NewYork": (time(8, 0), time(17, 0))
    }
    
    start_time, end_time = SESSION_TIMES.get(session_name, (None, None))
    if start_time is None:
        return None, None

    day_str = current_day.strftime('%Y-%m-%d')
    if start_time > end_time: # Handle overnight sessions like Asia
        prev_day_str = (current_day - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        mask = ((df_m1.index >= f"{prev_day_str} {start_time}") & (df_m1.index <= f"{day_str} {end_time}"))
    else:
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
    for tf in ['W1', 'D1', 'H4', 'H1']:
        if tf in all_data and not all_data[tf].empty:
            prev_bar = get_previous_bar(all_data[tf], current_time)
            if prev_bar is not None:
                levels[f'prev_{tf}_high'] = prev_bar['high']
                levels[f'prev_{tf}_low'] = prev_bar['low']

    if 'M1' in all_data and not all_data['M1'].empty:
        current_day = current_time.normalize()
        for session in ['Asia', 'London', 'NewYork']:
            sh, sl = get_session_high_low(all_data['M1'], session, current_day)
            if sh is not None: levels[f'{session}_high'] = sh
            if sl is not None: levels[f'{session}_low'] = sl
    return levels