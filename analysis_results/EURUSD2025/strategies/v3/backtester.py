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
from utils.pattern_engine import get_key_levels
from utils.account_manager import TradingAccount
from utils.reporting import generate_report

def calculate_key_levels(all_data, current_time):
    """Calculate all key levels for a given timestamp"""
    levels = {}
    
    # Calculate daily levels (previous day)
    prev_day = all_data['D1'][all_data['D1'].index < current_time].iloc[-1] if not all_data['D1'].empty else None
    if prev_day is not None:
        levels['prev_d_high'] = prev_day['high']
        levels['prev_d_low'] = prev_day['low']
    
    # Calculate weekly levels (previous week)
    prev_week = all_data['W1'][all_data['W1'].index < current_time].iloc[-1] if not all_data['W1'].empty else None
    if prev_week is not None:
        levels['prev_w_high'] = prev_week['high']
    
    # Calculate H4 levels (previous H4)
    prev_h4 = all_data['H4'][all_data['H4'].index < current_time].iloc[-1] if not all_data['H4'].empty else None
    if prev_h4 is not None:
        levels['prev_h4_high'] = prev_h4['high']
        levels['prev_h4_low'] = prev_h4['low']
    
    # Calculate H1 levels (previous H1)
    prev_h1 = all_data['H1'][all_data['H1'].index < current_time].iloc[-1] if not all_data['H1'].empty else None
    if prev_h1 is not None:
        levels['prev_h1_high'] = prev_h1['high']
        levels['prev_h1_low'] = prev_h1['low']
    
    # Calculate session levels (previous session 00:00-24:00 UTC)
    prev_session = all_data['M15'][
        (all_data['M15'].index >= (current_time - timedelta(days=1)).replace(hour=0, minute=0, second=0)) &
        (all_data['M15'].index < current_time.replace(hour=0, minute=0, second=0))
    ]
    if not prev_session.empty:
        levels['prev_session_high'] = prev_session['high'].max()
        levels['prev_session_low'] = prev_session['low'].min()
    
    return levels

def check_momentum_break(candle, level_price, direction):
    """Check if candle breaks a level with momentum"""
    if direction == 'long':
        return candle['close'] > level_price * 1.0001 and candle['close'] > candle['open']
    else:  # short
        return candle['close'] < level_price * 0.9999 and candle['close'] < candle['open']

def check_liquidity_sweep(candle, level_price, direction):
    """Check if candle sweeps a level and closes back"""
    if direction == 'long':
        return (candle['high'] > level_price * 1.001 and 
                candle['close'] < level_price and 
                candle['close'] > candle['open'])
    else:  # short
        return (candle['low'] < level_price * 0.999 and 
                candle['close'] > level_price and 
                candle['close'] < candle['open'])

def calculate_stop_loss(entry_price, level_price, trade_type, entry_type):
    """Calculate stop loss based on trade type and entry"""
    if entry_type == 'momentum_break':
        if trade_type == 'BUY':
            return level_price * 0.999
        else:  # SELL
            return level_price * 1.001
    else:  # liquidity_sweep
        if trade_type == 'BUY':
            return entry_price * 0.999  # Beyond sweep extreme
        else:  # SELL
            return entry_price * 1.001  # Beyond sweep extreme

def calculate_take_profit(entry_price, trade_type):
    """Calculate take profit levels"""
    # TP1: 0.1% scalping target
    if trade_type == 'BUY':
        return entry_price * 1.001
    else:  # SELL
        return entry_price * 0.999

def run_backtest(data_file):
    """Main backtest execution function"""
    print("Loading data...")
    all_data = load_and_prepare_data(data_file)
    if all_data is None:
        print("Failed to load data")
        return
    
    # Initialize trading account
    account = TradingAccount(initial_balance=10000.0)
    
    # Get M15 data for trading
    df_m15 = all_data['M15']
    
    # Track daily performance
    current_day = None
    daily_trades = 0
    daily_pnl = 0
    
    print("Running backtest...")
    for i, (timestamp, candle) in enumerate(df_m15.iterrows()):
        # Reset daily counters
        if current_day != timestamp.date():
            current_day = timestamp.date()
            daily_trades = 0
            daily_pnl = 0
        
        # Skip if we've hit daily limits
        if daily_trades >= 10 or daily_pnl <= -200:
            continue
        
        # Calculate key levels
        key_levels = calculate_key_levels(all_data, timestamp)
        
        # Check for open trades
        account.check_open_trades(timestamp, candle)
        
        # Skip if we have an open trade
        if account.open_trades:
            continue
        
        # Check all key levels for potential entries
        for level_name, level_price in key_levels.items():
            # Check if price is near level (within 0.05%)
            if abs(candle['close'] - level_price) / level_price <= 0.0005:
                
                # Momentum Break Entry
                if 'high' in level_name:  # Resistance level
                    if check_momentum_break(candle, level_price, 'long'):
                        sl_price = calculate_stop_loss(candle['close'], level_price, 'BUY', 'momentum_break')
                        tp_price = calculate_take_profit(candle['close'], 'BUY')
                        
                        account.open_trade(
                            entry_time=timestamp,
                            entry_price=candle['close'],
                            sl_price=sl_price,
                            trade_type='BUY',
                            reason=f"Momentum break at {level_name}",
                            context={'level_type': level_name},
                            tp_price=tp_price
                        )
                        daily_trades += 1
                        break
                
                elif 'low' in level_name:  # Support level
                    if check_momentum_break(candle, level_price, 'short'):
                        sl_price = calculate_stop_loss(candle['close'], level_price, 'SELL', 'momentum_break')
                        tp_price = calculate_take_profit(candle['close'], 'SELL')
                        
                        account.open_trade(
                            entry_time=timestamp,
                            entry_price=candle['close'],
                            sl_price=sl_price,
                            trade_type='SELL',
                            reason=f"Momentum break at {level_name}",
                            context={'level_type': level_name},
                            tp_price=tp_price
                        )
                        daily_trades += 1
                        break
                
                # Liquidity Sweep Fade Entry (only for high probability levels)
                if level_name in ['prev_d_low', 'prev_w_high']:
                    if 'low' in level_name:  # Support level sweep
                        if check_liquidity_sweep(candle, level_price, 'long'):
                            sl_price = calculate_stop_loss(candle['close'], level_price, 'BUY', 'liquidity_sweep')
                            tp_price = calculate_take_profit(candle['close'], 'BUY')
                            
                            account.open_trade(
                                entry_time=timestamp,
                                entry_price=candle['close'],
                                sl_price=sl_price,
                                trade_type='BUY',
                                reason=f"Liquidity sweep fade at {level_name}",
                                context={'level_type': level_name},
                                tp_price=tp_price
                            )
                            daily_trades += 1
                            break
                    
                    elif 'high' in level_name:  # Resistance level sweep
                        if check_liquidity_sweep(candle, level_price, 'short'):
                            sl_price = calculate_stop_loss(candle['close'], level_price, 'SELL', 'liquidity_sweep')
                            tp_price = calculate_take_profit(candle['close'], 'SELL')
                            
                            account.open_trade(
                                entry_time=timestamp,
                                entry_price=candle['close'],
                                sl_price=sl_price,
                                trade_type='SELL',
                                reason=f"Liquidity sweep fade at {level_name}",
                                context={'level_type': level_name},
                                tp_price=tp_price
                            )
                            daily_trades += 1
                            break
    
    print("Backtest complete. Generating report...")
    
    # Create results directory
    results_dir = os.path.join(script_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate comprehensive report
    generate_report(account, df_m15, results_dir, "eurusd_momentum_scalper")
    
    print(f"Results saved to {results_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='EUR/USD Momentum Scalper Backtester')
    parser.add_argument('data_file', help='Path to the 1-minute data CSV file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data_file):
        print(f"Error: File not found at '{args.data_file}'")
        sys.exit(1)
    
    run_backtest(args.data_file)