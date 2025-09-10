import pandas as pd
from datetime import time

# Define session times in UTC
SESSION_TIMES = {
    "Asia": (time(20, 0), time(5, 0)),
    "London": (time(3, 0), time(12, 0)),
    "NewYork": (time(8, 0), time(17, 0))
}

def get_previous_bar(df, current_time):
    """
    Gets the most recent bar from a dataframe that closed *before* the current time.
    Pure OHLC function - no volume or indicator dependencies.
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
        for session in SESSION_TIMES.keys():
            sh, sl = get_session_high_low(all_data['M1'], session, current_day)
            if sh is not None: levels[f'{session}_high'] = sh
            if sl is not None: levels[f'{session}_low'] = sl
    return levels

def detect_fvg(candle1, candle2, candle3):
    """
    Detects a Fair Value Gap (FVG) from three consecutive candles using pure OHLC data.
    """
    # Check for bullish FVG (gap between candle 1 high and candle 3 low)
    if float(candle3['low']) > float(candle1['high']):
        return 'bullish', float(candle3['low']), float(candle1['high'])
    # Check for bearish FVG (gap between candle 1 low and candle 3 high)
    if float(candle3['high']) < float(candle1['low']):
        return 'bearish', float(candle1['low']), float(candle3['high'])
    return None, None, None

def detect_citsd(current_candle, previous_candle):
    """
    Detects a Change in The State of Delivery (CITSD).
    """
    # Bullish: Current candle is up, and current close is >= previous high
    is_bullish = (current_candle['close'] > current_candle['open'] and
                  current_candle['close'] >= previous_candle['high'])
    if is_bullish:
        return 'bullish'
    # Bearish: Current candle is down, and current close is <= previous low
    is_bearish = (current_candle['close'] < current_candle['open'] and
                  current_candle['close'] <= previous_candle['low'])
    if is_bearish:
        return 'bearish'
    return None

def check_manipulation_or_breach(m1_candle, level_price, level_type):
    """
    Checks if a 1-min candle manipulated or breached a key level.
    """
    if level_type == 'high':
        if m1_candle['high'] > level_price:
            return 'manipulation' if m1_candle['close'] < level_price else 'breach'
    elif level_type == 'low':
        if m1_candle['low'] < level_price:
            return 'manipulation' if m1_candle['close'] > level_price else 'breach'
    return None

def find_confirmation_sequence(confirmation_df, interaction, level_type):
    """
    Analyzes a block of candles to find a sequential confirmation pattern.
    """
    if confirmation_df.empty or len(confirmation_df) < 5: return None
    trade_type = 'BUY' if (interaction == 'manipulation' and level_type == 'low') or \
                          (interaction == 'breach' and level_type == 'high') else 'SELL'
    
    citsd_found_at_idx = -1
    
    # Step 1: Find the initial CITSD
    for j in range(1, len(confirmation_df)):
        prev_m1, curr_m1 = confirmation_df.iloc[j-1], confirmation_df.iloc[j]
        citsd_type = detect_citsd(curr_m1, prev_m1)
        if (trade_type == 'BUY' and citsd_type == 'bullish') or (trade_type == 'SELL' and citsd_type == 'bearish'):
            citsd_found_at_idx = j
            break

    if citsd_found_at_idx == -1:
        return None

    # Step 2: Look for FVG or FVG Inversion after the CITSD
    for k in range(citsd_found_at_idx + 2, len(confirmation_df)):
        c1, c2, c3 = confirmation_df.iloc[k-2], confirmation_df.iloc[k-1], confirmation_df.iloc[k]
        
        # Check for FVG in our direction
        fvg_type, _, _ = detect_fvg(c1, c2, c3)
        if (trade_type == 'BUY' and fvg_type == 'bullish') or (trade_type == 'SELL' and fvg_type == 'bearish'):
            sl_price = c1['low'] if trade_type == 'BUY' else c1['high']
            return {'entry_candle': c3, 'sl_price': sl_price, 'trade_type': trade_type}

        # Check for FVG Inversion
        opposing_fvg_type = 'bearish' if trade_type == 'BUY' else 'bullish'
        fvg_type, fvg_top, fvg_bottom = detect_fvg(c1, c2, c3)
        if fvg_type == opposing_fvg_type:
            # Check if any subsequent candle in the window inverts it
            for l in range(k + 1, len(confirmation_df)):
                inversion_candle = confirmation_df.iloc[l]
                if trade_type == 'BUY' and inversion_candle['close'] > fvg_top:
                    sl_price = c1['low'] 
                    return {'entry_candle': inversion_candle, 'sl_price': sl_price, 'trade_type': trade_type}
                elif trade_type == 'SELL' and inversion_candle['close'] < fvg_bottom:
                    sl_price = c1['high']
                    return {'entry_candle': inversion_candle, 'sl_price': sl_price, 'trade_type': trade_type}
    return None

def find_recent_fvgs(df, end_time, lookback_period=30):
    """
    Finds recent, unfilled, and non-invalidated FVGs on a given dataframe.
    """
    subset = df[df.index <= end_time].tail(lookback_period + 10)
    if len(subset) < 3:
        return []

    valid_fvgs = []
    for i in range(len(subset) - 2 - 10, len(subset) - 2):
        if i < 0: continue
        c1, c2, c3 = subset.iloc[i], subset.iloc[i+1], subset.iloc[i+2]
        fvg_type, top, bottom = detect_fvg(c1, c2, c3)

        if fvg_type:
            is_invalidated = False
            candles_after_fvg = subset.iloc[i+3:]
            for _, future_candle in candles_after_fvg.iterrows():
                if fvg_type == 'bullish' and future_candle['close'] < bottom:
                    is_invalidated = True
                    break
                if fvg_type == 'bearish' and future_candle['close'] > top:
                    is_invalidated = True
                    break

            if not is_invalidated:
                valid_fvgs.append({
                    'type': fvg_type,
                    'top': top,
                    'bottom': bottom,
                    'timestamp': c2.name
                })
    return valid_fvgs

def find_recent_swing_point(df, end_time, trade_type, lookback_period=20):
    """
    Finds the most recent significant swing high or swing low.
    """
    subset = df[df.index < end_time].tail(lookback_period)
    if len(subset) < 3:
        return None

    for i in range(len(subset) - 2, 0, -1):
        prev_c, current_c, next_c = subset.iloc[i-1], subset.iloc[i], subset.iloc[i+1]

        if trade_type == 'BUY':
            if current_c['low'] < prev_c['low'] and current_c['low'] < next_c['low']:
                return current_c['low']
        elif trade_type == 'SELL':
            if current_c['high'] > prev_c['high'] and current_c['high'] > next_c['high']:
                return current_c['high']

    return None