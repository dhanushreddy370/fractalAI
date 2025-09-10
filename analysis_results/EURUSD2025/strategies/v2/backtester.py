import sys
import os
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the script's own directory to the Python path to ensure local modules can be found.
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from utils.data_handler import load_and_prepare_data
from utils.pattern_engine import get_key_levels, is_within_percentage
from utils.account_manager import TradingAccount
from utils.reporting import generate_report

def calculate_key_levels(all_data, current_time):
    """Calculate all key levels for the current time"""
    levels = {}
    
    # Get previous day levels
    prev_day = get_previous_bar(all_data['D1'], current_time)
    if prev_day is not None:
        levels['prev_d_high'] = prev_day['high']
        levels['prev_d_low'] = prev_day['low']
    
    # Get previous week high (Friday close)
    prev_week = get_previous_bar(all_data['W1'], current_time)
    if prev_week is not None:
        levels['prev_w_high'] = prev_week['high']
    
    # Get previous H4 levels
    prev_h4 = get_previous_bar(all_data['H4'], current_time)
    if prev_h4 is not None:
        levels['prev_h4_high'] = prev_h4['high']
        levels['prev_h4_low'] = prev_h4['low']
    
    # Get previous H1 levels
    prev_h1 = get_previous_bar(all_data['H1'], current_time)
    if prev_h1 is not None:
        levels['prev_h1_high'] = prev_h1['high']
        levels['prev_h1_low'] = prev_h1['low']
    
    # Get previous session levels (00:00-24:00 UTC)
    current_day_start = current_time.normalize()
    prev_day_start = current_day_start - timedelta(days=1)
    
    prev_session_data = all_data['M1'].loc[prev_day_start:current_day_start]
    if not prev_session_data.empty:
        levels['prev_session_high'] = prev_session_data['high'].max()
        levels['prev_session_low'] = prev_session_data['low'].min()
    
    return levels

def check_momentum_break_entry(current_candle, key_levels, trade_type):
    """Check for momentum break entry conditions"""
    for level_name, level_price in key_levels.items():
        if level_price is None:
            continue
            
        # Check if price is within 0.05% of the level
        if not is_within_percentage(current_candle['close'], level_price, 0.0005):
            continue
            
        # Determine expected break direction based on level type
        if 'high' in level_name and trade_type == 'BUY':
            # Bullish break: close above level by at least 0.01%
            if current_candle['close'] > level_price * 1.0001:
                return level_name, level_price
                
        elif 'low' in level_name and trade_type == 'SELL':
            # Bearish break: close below level by at least 0.01%
            if current_candle['close'] < level_price * 0.9999:
                return level_name, level_price
    
    return None, None

def check_sweep_fade_entry(current_candle, prev_candle, key_levels, trade_type):
    """Check for liquidity sweep fade entry conditions"""
    for level_name, level_price in key_levels.items():
        if level_price is None:
            continue
            
        # Check sweep probabilities (simplified)
        sweep_prob = 0.0
        if level_name == 'prev_d_low':
            sweep_prob = 0.4772
        elif level_name == 'prev_d_high':
            sweep_prob = 0.4329
        elif level_name == 'prev_w_high':
            sweep_prob = 0.4868
        
        if sweep_prob < 0.4:
            continue
            
        # Check for sweep pattern
        if 'high' in level_name and trade_type == 'SELL':
            # Price exceeded level by 0.1% but closed back within
            if (prev_candle['high'] > level_price * 1.001 and 
                current_candle['close'] <= level_price):
                return level_name, level_price
                
        elif 'low' in level_name and trade_type == 'BUY':
            # Price exceeded level by 0.1% but closed back within
            if (prev_candle['low'] < level_price * 0.999 and 
                current_candle['close'] >= level_price):
                return level_name, level_price
    
    return None, None

def calculate_stop_loss(entry_price, level_price, trade_type, entry_type):
    """Calculate stop loss based on entry type"""
    if entry_type == 'momentum_break':
        # SL at opposite side of the key level
        if trade_type == 'BUY':
            return level_price * 0.999  # 0.1% below level
        else:
            return level_price * 1.001  # 0.1% above level
    else:  # sweep_fade
        # SL beyond the extreme of the sweep
        if trade_type == 'BUY':
            return level_price * 0.999  # 0.1% below level
        else:
            return level_price * 1.001  # 0.1% above level

def main():
    parser = argparse.ArgumentParser(description='EUR/USD Momentum Scalper Backtester')
    parser.add_argument('data_file', help='Path to the 1-minute data CSV file')
    args = parser.parse_args()
    
    # Load and prepare data
    all_data = load_and_prepare_data(args.data_file)
    if all_data is None:
        print("Failed to load data. Exiting.")
        return
    
    # Initialize trading account
    account = TradingAccount(initial_balance=10000.0)
    
    # Get M15 data for trading
    df_m15 = all_data['M15']
    
    # Track daily metrics
    current_date = None
    daily_trades = 0
    daily_pnl = 0
    
    # Main backtest loop
    for i in range(1, len(df_m15)):
        current_time = df_m15.index[i]
        current_candle = df_m15.iloc[i]
        prev_candle = df_m15.iloc[i-1]
        
        # Check if it's a new day
        if current_date != current_time.date():
            current_date = current_time.date()
            daily_trades = 0
            daily_pnl = 0
        
        # Skip if daily loss cap reached
        if daily_pnl <= -200:  # 2% of $10,000
            continue
            
        # Skip if max trades reached
        if daily_trades >= 10:
            continue
            
        # Skip if there are open trades
        if account.open_trades:
            continue
            
        # Calculate key levels
        key_levels = calculate_key_levels(all_data, current_time)
        
        # Check for momentum break entries
        for trade_type in ['BUY', 'SELL']:
            level_name, level_price = check_momentum_break_entry(current_candle, key_levels, trade_type)
            if level_name:
                sl_price = calculate_stop_loss(current_candle['close'], level_price, trade_type, 'momentum_break')
                
                # Open trade
                account.open_trade(
                    entry_time=current_time,
                    entry_price=current_candle['close'],
                    sl_price=sl_price,
                    trade_type=trade_type,
                    reason=f"Momentum break at {level_name}",
                    context={
                        'level_type': level_name,
                        'level_price': level_price,
                        'entry_type': 'momentum_break'
                    }
                )
                daily_trades += 1
                break
        
        # Check for sweep fade entries if no momentum break found
        if not account.open_trades:
            for trade_type in ['BUY', 'SELL']:
                level_name, level_price = check_sweep_fade_entry(current_candle, prev_candle, key_levels, trade_type)
                if level_name:
                    sl_price = calculate_stop_loss(current_candle['close'], level_price, trade_type, 'sweep_fade')
                    
                    # Open trade
                    account.open_trade(
                        entry_time=current_time,
                        entry_price=current_candle['close'],
                        sl_price=sl_price,
                        trade_type=trade_type,
                        reason=f"Sweep fade at {level_name}",
                        context={
                            'level_type': level_name,
                            'level_price': level_price,
                            'entry_type': 'sweep_fade'
                        }
                    )
                    daily_trades += 1
                    break
        
        # Check open trades for exits
        trade_log = account.check_open_trades(current_time, current_candle)
        if trade_log:
            daily_pnl += trade_log['net_pnl']
    
    # Generate results
    results_dir = os.path.join(script_dir, 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    generate_report(account, df_m15, results_dir, "eurusd_momentum_scalper")
    
    print(f"Backtest completed. Results saved to {results_dir}")

if __name__ == "__main__":
    main()