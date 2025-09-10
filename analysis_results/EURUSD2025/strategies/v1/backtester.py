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

class EURUSDMomentumScalper:
    def __init__(self, account, all_data):
        self.account = account
        self.all_data = all_data
        self.df_m15 = all_data['M15']
        self.current_position = None
        self.daily_trade_count = 0
        self.daily_pnl = 0
        self.last_trade_date = None
        
        # Key levels priority order
        self.key_levels_priority = [
            'prev_D1_high', 'prev_D1_low',
            'prev_W1_high',
            'prev_Session_high', 'prev_Session_low',
            'prev_H4_high', 'prev_H4_low',
            'prev_H1_high', 'prev_H1_low'
        ]
    
    def reset_daily_counts(self, current_date):
        """Reset daily trade count and P&L if it's a new day"""
        if self.last_trade_date != current_date:
            self.daily_trade_count = 0
            self.daily_pnl = 0
            self.last_trade_date = current_date
    
    def can_trade_today(self):
        """Check if daily limits are exceeded"""
        return self.daily_trade_count < 10 and self.daily_pnl > -0.02 * self.account.initial_balance
    
    def check_momentum_break_entry(self, current_candle, current_time, key_levels):
        """Check for momentum break entry conditions"""
        for level_name in self.key_levels_priority:
            if level_name not in key_levels:
                continue
                
            level_price = key_levels[level_name]
            
            # Check if price is within 0.05% of the level
            if not is_within_percentage(current_candle['close'], level_price, 0.0005):
                continue
            
            # Determine direction based on level type
            if 'high' in level_name:
                # Long entry: break above resistance
                if (current_candle['close'] > level_price and 
                    current_candle['close'] > current_candle['open'] and
                    abs(current_candle['close'] - level_price) >= abs(current_candle['open'] - current_candle['close'])):
                    
                    sl_price = level_price * 0.999  # SL at level minus 0.1%
                    tp_price = current_candle['close'] * 1.001  # TP at 0.1%
                    
                    return {
                        'trade_type': 'BUY',
                        'entry_price': current_candle['close'],
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'reason': f'Momentum break above {level_name}',
                        'context': {'key_level': level_name, 'level_type': 'high'}
                    }
            
            elif 'low' in level_name:
                # Short entry: break below support
                if (current_candle['close'] < level_price and 
                    current_candle['close'] < current_candle['open'] and
                    abs(level_price - current_candle['close']) >= abs(current_candle['open'] - current_candle['close'])):
                    
                    sl_price = level_price * 1.001  # SL at level plus 0.1%
                    tp_price = current_candle['close'] * 0.999  # TP at 0.1%
                    
                    return {
                        'trade_type': 'SELL',
                        'entry_price': current_candle['close'],
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'reason': f'Momentum break below {level_name}',
                        'context': {'key_level': level_name, 'level_type': 'low'}
                    }
        
        return None
    
    def check_sweep_fade_entry(self, current_candle, prev_candle, current_time, key_levels):
        """Check for liquidity sweep fade entry conditions"""
        for level_name in ['prev_D1_low', 'prev_W1_high']:
            if level_name not in key_levels:
                continue
                
            level_price = key_levels[level_name]
            
            # Check for sweep pattern
            if 'low' in level_name:
                # Bullish sweep fade: price sweeps below support then closes back above
                if (prev_candle['low'] < level_price * 0.999 and  # Swept by 0.1%
                    current_candle['close'] > level_price and
                    current_candle['close'] > current_candle['open']):
                    
                    sl_price = prev_candle['low'] * 0.999  # SL beyond sweep extreme
                    tp_price = current_candle['close'] * 1.001  # TP at 0.1%
                    
                    return {
                        'trade_type': 'BUY',
                        'entry_price': current_candle['close'],
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'reason': f'Sweep fade at {level_name}',
                        'context': {'key_level': level_name, 'level_type': 'low'}
                    }
            
            elif 'high' in level_name:
                # Bearish sweep fade: price sweeps above resistance then closes back below
                if (prev_candle['high'] > level_price * 1.001 and  # Swept by 0.1%
                    current_candle['close'] < level_price and
                    current_candle['close'] < current_candle['open']):
                    
                    sl_price = prev_candle['high'] * 1.001  # SL beyond sweep extreme
                    tp_price = current_candle['close'] * 0.999  # TP at 0.1%
                    
                    return {
                        'trade_type': 'SELL',
                        'entry_price': current_candle['close'],
                        'sl_price': sl_price,
                        'tp_price': tp_price,
                        'reason': f'Sweep fade at {level_name}',
                        'context': {'key_level': level_name, 'level_type': 'high'}
                    }
        
        return None
    
    def check_time_exit(self, trade, current_time):
        """Check if trade should be exited due to time limit"""
        if 'entry_time' in trade:
            entry_time = trade['entry_time']
            if (current_time - entry_time) >= timedelta(minutes=60):  # 4 M15 candles
                return current_candle['close']  # Exit at current price
        return None
    
    def run_backtest(self):
        """Main backtest loop"""
        print("Running EUR/USD Momentum Scalper backtest...")
        
        for i in range(1, len(self.df_m15)):
            current_time = self.df_m15.index[i]
            current_candle = self.df_m15.iloc[i]
            prev_candle = self.df_m15.iloc[i-1]
            
            # Reset daily counts if new day
            self.reset_daily_counts(current_time.date())
            
            # Skip if we can't trade today
            if not self.can_trade_today():
                continue
            
            # Get key levels for current time
            key_levels = get_key_levels(self.all_data, current_time)
            
            # Check for entries only if no current position
            if not self.account.open_trades:
                # Check momentum break entry first
                trade_params = self.check_momentum_break_entry(current_candle, current_time, key_levels)
                
                # If no momentum break, check sweep fade
                if not trade_params:
                    trade_params = self.check_sweep_fade_entry(current_candle, prev_candle, current_time, key_levels)
                
                # Open trade if conditions met
                if trade_params:
                    self.account.open_trade(
                        entry_time=current_time,
                        entry_price=trade_params['entry_price'],
                        sl_price=trade_params['sl_price'],
                        trade_type=trade_params['trade_type'],
                        reason=trade_params['reason'],
                        context=trade_params['context'],
                        tp_price=trade_params['tp_price']
                    )
                    self.daily_trade_count += 1
            
            # Check open trades for exits
            closed_trade = self.account.check_open_trades(current_time, current_candle)
            if closed_trade:
                self.daily_pnl += closed_trade['net_pnl']
            
            # Check for time-based exits
            for trade in self.account.open_trades:
                exit_price = self.check_time_exit(trade, current_time)
                if exit_price:
                    closed_trade = self.account.close_trade(trade, current_time, exit_price, True)
                    if closed_trade:
                        self.daily_pnl += closed_trade['net_pnl']

        print("Backtest completed.")

def main():
    parser = argparse.ArgumentParser(description='EUR/USD Momentum Scalper Backtester')
    parser.add_argument('data_file', help='Path to the 1-minute data CSV file')
    args = parser.parse_args()
    
    # Load and prepare data
    all_data = load_and_prepare_data(args.data_file)
    if not all_data:
        print("Failed to load data. Exiting.")
        return
    
    # Create results directory
    results_dir = os.path.join(script_dir, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    # Initialize account and strategy
    account = TradingAccount(initial_balance=10000.0)
    strategy = EURUSDMomentumScalper(account, all_data)
    
    # Run backtest
    strategy.run_backtest()
    
    # Generate report
    generate_report(account, all_data['M15'], results_dir, "eurusd_momentum_scalper")
    
    print(f"Results saved to: {results_dir}")

if __name__ == "__main__":
    main()