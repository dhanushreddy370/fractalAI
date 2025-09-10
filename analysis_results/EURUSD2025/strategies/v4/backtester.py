import sys
import os
import argparse
import pandas as pd
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
    """Calculate all key levels for a given timestamp"""
    levels = {}
    
    # Calculate daily levels (previous day)
    prev_day = current_time - timedelta(days=1)
    prev_day_data = all_data['D1'][all_data['D1'].index.date == prev_day.date()]
    if not prev_day_data.empty:
        levels['prev_d_high'] = prev_day_data['high'].max()
        levels['prev_d_low'] = prev_day_data['low'].min()
    
    # Calculate weekly levels (previous week)
    prev_week = current_time - timedelta(weeks=1)
    prev_week_data = all_data['W1'][all_data['W1'].index <= prev_week]
    if not prev_week_data.empty:
        levels['prev_w_high'] = prev_week_data['high'].max()
    
    # Calculate H4 levels
    prev_h4_data = all_data['H4'][all_data['H4'].index < current_time]
    if not prev_h4_data.empty:
        levels['prev_h4_high'] = prev_h4_data.iloc[-1]['high']
        levels['prev_h4_low'] = prev_h4_data.iloc[-1]['low']
    
    # Calculate H1 levels
    prev_h1_data = all_data['H1'][all_data['H1'].index < current_time]
    if not prev_h1_data.empty:
        levels['prev_h1_high'] = prev_h1_data.iloc[-1]['high']
        levels['prev_h1_low'] = prev_h1_data.iloc[-1]['low']
    
    # Calculate session levels (previous session 00:00-24:00 UTC)
    prev_session_date = (current_time - timedelta(days=1)).date()
    session_data = all_data['M1'][
        (all_data['M1'].index.date == prev_session_date) & 
        (all_data['M1'].index.hour >= 0) & 
        (all_data['M1'].index.hour < 24)
    ]
    if not session_data.empty:
        levels['prev_session_high'] = session_data['high'].max()
        levels['prev_session_low'] = session_data['low'].min()
    
    return levels

def check_momentum_break(candle, level_type, level_price, direction):
    """Check if candle breaks a level with momentum"""
    if direction == 'long':
        return (candle['close'] > level_price and 
                candle['close'] - candle['open'] >= abs(level_price - candle['open']) * 0.999)
    else:  # short
        return (candle['close'] < level_price and 
                candle['open'] - candle['close'] >= abs(candle['open'] - level_price) * 0.999)

def check_sweep_fade(candle, level_type, level_price):
    """Check for liquidity sweep fade pattern"""
    if level_type.endswith('_high'):
        return (candle['high'] > level_price * 1.001 and 
                candle['close'] < level_price)
    else:  # level_type.endswith('_low')
        return (candle['low'] < level_price * 0.999 and 
                candle['close'] > level_price)

def run_backtest(data_file):
    """Main backtest execution function"""
    print("Loading data...")
    all_data = load_and_prepare_data(data_file)
    if all_data is None:
        return
    
    print("Initializing trading account...")
    account = TradingAccount(initial_balance=10000.0)
    
    df_m15 = all_data['M15']
    trade_count_today = 0
    daily_pnl = 0
    current_date = None
    
    print("Running backtest...")
    for i, (timestamp, candle) in enumerate(df_m15.iterrows()):
        # Reset daily counters on new day
        if current_date != timestamp.date():
            trade_count_today = 0
            daily_pnl = 0
            current_date = timestamp.date()
        
        # Check daily limits
        if trade_count_today >= 10 or daily_pnl <= -200:
            continue
        
        # Calculate key levels
        key_levels = calculate_key_levels(all_data, timestamp)
        
        # Check for open trades
        account.check_open_trades(timestamp, candle)
        
        # Skip if already in a trade
        if account.open_trades:
            continue
        
        # Check all key levels for entry opportunities
        for level_name, level_price in key_levels.items():
            if level_price is None:
                continue
            
            # Check if price is near level
            if is_within_percentage(candle['close'], level_price, 0.05):
                
                # Momentum Break Entry
                if level_name.endswith('_high'):
                    if check_momentum_break(candle, level_name, level_price, 'long'):
                        sl_price = level_price * 0.999
                        account.open_trade(
                            timestamp, candle['close'], sl_price, 'BUY', 
                            f'Momentum break {level_name}',
                            {'level_type': level_name, 'level_price': level_price}
                        )
                        trade_count_today += 1
                        break
                
                elif level_name.endswith('_low'):
                    if check_momentum_break(candle, level_name, level_price, 'short'):
                        sl_price = level_price * 1.001
                        account.open_trade(
                            timestamp, candle['close'], sl_price, 'SELL',
                            f'Momentum break {level_name}',
                            {'level_type': level_name, 'level_price': level_price}
                        )
                        trade_count_today += 1
                        break
                
                # Liquidity Sweep Fade Entry (only for high probability levels)
                if level_name in ['prev_d_low', 'prev_d_high', 'prev_w_high']:
                    if check_sweep_fade(candle, level_name, level_price):
                        if level_name.endswith('_high'):
                            sl_price = candle['high'] * 1.001
                            account.open_trade(
                                timestamp, candle['close'], sl_price, 'SELL',
                                f'Sweep fade {level_name}',
                                {'level_type': level_name, 'level_price': level_price}
                            )
                        else:
                            sl_price = candle['low'] * 0.999
                            account.open_trade(
                                timestamp, candle['close'], sl_price, 'BUY',
                                f'Sweep fade {level_name}',
                                {'level_type': level_name, 'level_price': level_price}
                            )
                        trade_count_today += 1
                        break
    
    print("Backtest complete. Generating report...")
    
    # Create results directory
    results_dir = os.path.join(script_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate report
    generate_report(account, df_m15, results_dir, "eurusd_momentum_scalper")
    
    print(f"Results saved to {results_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EUR/USD Momentum Scalper Backtester')
    parser.add_argument('data_file', help='Path to the 1-minute data CSV file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_file):
        print(f"Error: File '{args.data_file}' not found")
        sys.exit(1)
    
    run_backtest(args.data_file)