"""
The "Hands" of the FractalAI Suite.

This module performs pure OHLC-based quantitative analysis. No technical indicators
(e.g., ATR/RSI/MA) and no order-flow/volume are used. It includes DST-aware session
calculations and analyzes reactions at session highs/lows and higher timeframe key
levels.

v3.0 - Pure OHLC mode: removed ATR usage and replaced with candle-range proximity.
"""
import pandas as pd
import numpy as np
import os
import json
from tqdm import tqdm
from collections import defaultdict

# --- Configuration Constants (OHLC-only) ---
LEVEL_PROXIMITY_MULTIPLIER = 0.75  # How close current candle must be to a level relative to its own range
REACTION_WINDOW = 10               # Number of M1 candles to observe after touching a level

# --- DST-Aware Session Definitions (UTC) ---
def get_session_hours(timestamp):
    """Returns DST-aware session times in UTC."""
    month = timestamp.month
    # A simple month-based approximation for DST
    is_dst_us = 3 <= month <= 10
    is_dst_eu = 4 <= month <= 9
    
    sessions = {
        'asian': (0, 9),
        'london': (7, 16) if is_dst_eu else (8, 17),
        'new_york': (12, 21) if is_dst_us else (13, 22)
    }
    return sessions

def get_session(timestamp):
    """Identifies the session for a given timestamp."""
    sessions = get_session_hours(timestamp)
    hour = timestamp.hour
    if sessions['asian'][0] <= hour < sessions['asian'][1]:
        return 'asian'
    if sessions['london'][0] <= hour < sessions['london'][1]:
        return 'london'
    if sessions['new_york'][0] <= hour < sessions['new_york'][1]:
        return 'new_york'
    return 'off_session'

def run(data_path: str, output_dir: str) -> str:
    """Executes the full quantitative analysis pipeline."""
    print("   - [Engine] Loading and preparing data...")
    df = pd.read_csv(data_path)
    df['time'] = pd.to_datetime(df['time'])
    df.drop_duplicates(subset=['time'], inplace=True)
    df.set_index('time', inplace=True)
    df.dropna(inplace=True)

    print("   - [Engine] Resampling for higher timeframes...")
    ohlc_dict = {'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}
    df_m15 = df.resample('15min').agg(ohlc_dict)
    df_h1 = df.resample('h').agg(ohlc_dict)
    df_h4 = df.resample('4h').agg(ohlc_dict)
    df_d = df.resample('D').agg(ohlc_dict)
    df_w = df.resample('W-MON').agg(ohlc_dict)
    
    print("   - [Engine] Calculating session highs and lows...")
    df['session'] = [get_session(ts) for ts in df.index]
    df['date'] = df.index.date
    
    session_ohlc = df.groupby(['date', 'session']).agg(
        session_high=('high', 'max'),
        session_low=('low', 'min')
    )
    
    session_ohlc_shifted = session_ohlc.groupby(level='date').shift(1)
    df = df.join(session_ohlc_shifted.rename(columns={
        'session_high': 'prev_session_high', 
        'session_low': 'prev_session_low'}), on=['date', 'session'])
    
    # FIX: Updated fillna to the modern ffill() syntax to remove the FutureWarning
    df.ffill(inplace=True)

    print("   - [Engine] Engineering key level features...")
    for tf_name, tf_df in [('h1', df_h1), ('h4', df_h4), ('d', df_d), ('w', df_w)]:
        df[f'prev_{tf_name}_high'] = tf_df['high'].shift(1).reindex(df.index, method='ffill')
        df[f'prev_{tf_name}_low'] = tf_df['low'].shift(1).reindex(df.index, method='ffill')

    # Pure OHLC volatility proxy: current candle range (no rolling indicator)
    df['candle_range'] = (df['high'] - df['low']).astype(float)
    df.dropna(inplace=True)

    print("   - [Engine] Analyzing intra-candle paths...")
    path_analysis_results = _analyze_paths(df, [('M15', df_m15), ('H1', df_h1), ('H4', df_h4)])

    print("   - [Engine] Analyzing key level reactions...")
    reaction_results, total_interactions = _analyze_level_reactions(df)
    
    print("   - [Engine] Assembling final JSON output...")
    output_data = {
        "analysis_metadata": { "input_file": os.path.basename(data_path), "total_m1_bars_analyzed": len(df) },
        "intra_candle_path_dynamics": path_analysis_results,
        "key_level_reaction_analysis": {
            "total_interactions_detected": total_interactions,
            "level_breakdown": reaction_results
        }
    }
    
    output_filename = f"{os.path.splitext(os.path.basename(data_path))[0]}_quantitative_output.json"
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    return output_path

def _analyze_paths(df, timeframes):
    path_analysis_results = {}
    for tf, tf_df_orig in timeframes:
        tf_df = tf_df_orig.dropna().copy()

        # FIX: Corrected the logic to generate valid pandas frequency strings
        if 'M' in tf:
            freq_str = tf.replace('M', '') + 'min' # Creates '15min'
        else: # 'H'
            freq_str = tf.replace('H', '') + 'h'   # Creates '1h', '4h'
        
        ohlc_indices = df.reset_index().groupby(pd.Grouper(key='time', freq=freq_str)).apply(
            lambda g: (g.index[0], g['high'].idxmax(), g['low'].idxmin(), g.index[-1]) if not g.empty else (-1,-1,-1,-1),
            include_groups=False
        ).reindex(tf_df.index)

        ohlc_indices.dropna(inplace=True)
        tf_df = tf_df.loc[ohlc_indices.index]

        open_indices, high_indices, low_indices, close_indices = zip(*ohlc_indices)
        is_bullish = tf_df['close'] > tf_df['open']
        
        tf_df['path_type'] = _classify_path_vectorized(open_indices, high_indices, low_indices, close_indices, is_bullish)
        results = tf_df['path_type'].value_counts(normalize=True) * 100
        path_analysis_results[tf] = {
            "efficient_trend_pct": results.get('Efficient Trend', 0),
            "reversal_pct": results.get('Reversal', 0),
            "indecisive_pct": results.get('Indecisive', 0)
        }
    return path_analysis_results

@np.vectorize
def _classify_path_vectorized(open_idx, high_idx, low_idx, close_idx, is_bullish):
    if high_idx == -1 or low_idx == -1: return "Indecisive"
    if is_bullish:
        return "Efficient Trend" if low_idx < high_idx else "Reversal"
    else:
        return "Efficient Trend" if high_idx < low_idx else "Reversal"

def _analyze_level_reactions(df):
    key_levels = {
        'Prev_Session_High': 'prev_session_high', 'Prev_Session_Low': 'prev_session_low',
        'Prev_H1_High': 'prev_h1_high', 'Prev_H1_Low': 'prev_h1_low',
        'Prev_H4_High': 'prev_h4_high', 'Prev_H4_Low': 'prev_h4_low',
        'Prev_D_High': 'prev_d_high', 'Prev_D_Low': 'prev_d_low',
        'Prev_W_High': 'prev_w_high', 'Prev_W_Low': 'prev_w_low'
    }
    reaction_results = defaultdict(lambda: defaultdict(int))
    total_interactions = 0

    for i in tqdm(range(len(df) - REACTION_WINDOW), desc="   - [Engine] Scanning Level Interactions", leave=False):
        row = df.iloc[i]
        candle_range = row['candle_range']
        if candle_range == 0 or pd.isna(candle_range):
            continue

        for level_name, col_name in key_levels.items():
            if col_name not in row or pd.isna(row[col_name]):
                continue
            level_price = float(row[col_name])
            is_high_level = 'High' in level_name

            # Proximity check based on current candle's own range (pure OHLC)
            if (is_high_level and abs(float(row['high']) - level_price) <= candle_range * LEVEL_PROXIMITY_MULTIPLIER) or \
               (not is_high_level and abs(float(row['low']) - level_price) <= candle_range * LEVEL_PROXIMITY_MULTIPLIER):
                
                total_interactions += 1
                window = df.iloc[i : i + REACTION_WINDOW]
                
                if is_high_level:
                    if window['high'].max() > level_price and window['close'].iloc[-1] < level_price:
                        reaction_results[level_name]['liquidity_sweep'] += 1
                    elif window['high'].max() > level_price and window['close'].iloc[-1] > level_price:
                        reaction_results[level_name]['breach_and_continue'] += 1
                    else:
                        reaction_results[level_name]['consolidation_rejection'] += 1
                else:
                    if window['low'].min() < level_price and window['close'].iloc[-1] > level_price:
                        reaction_results[level_name]['liquidity_sweep'] += 1
                    elif window['low'].min() < level_price and window['close'].iloc[-1] < level_price:
                        reaction_results[level_name]['breach_and_continue'] += 1
                    else:
                        reaction_results[level_name]['consolidation_rejection'] += 1
    
    final_results = {}
    for level, counts in reaction_results.items():
        total = sum(counts.values())
        final_results[level] = {
            "total_interactions": total,
            "liquidity_sweep_pct": (counts['liquidity_sweep'] / total * 100) if total > 0 else 0,
            "breach_continue_pct": (counts['breach_and_continue'] / total * 100) if total > 0 else 0,
            "consolidation_rejection_pct": (counts['consolidation_rejection'] / total * 100) if total > 0 else 0,
        }

    return final_results, total_interactions

