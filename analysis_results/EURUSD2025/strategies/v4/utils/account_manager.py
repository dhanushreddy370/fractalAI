import pandas as pd
import numpy as np

# --- Configuration for costs ---
COMMISSION_PER_LOT = 3.5
PIP_VALUE_PER_LOT = 10.0
PIP_SIZE = 0.0001
MAX_LOT_SIZE_CAP = 500.0
SPREAD_MEAN = 0.00005  # 0.5 pips
SPREAD_STD = 0.00001   # 0.1 pips variability
SLIPPAGE_MEAN = 0.00002  # 0.2 pips
SLIPPAGE_STD = 0.00001   # 0.1 pips variability

class TradingAccount:
    def __init__(self, initial_balance=10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.open_trades = []
        self.trade_log = []
        self.daily_trades = 0
        self.daily_pnl = 0

    def apply_market_friction(self, requested_price, trade_type):
        """Apply spread and slippage to trade execution"""
        spread = np.random.normal(SPREAD_MEAN, SPREAD_STD)
        slippage = np.random.normal(SLIPPAGE_MEAN, SLIPPAGE_STD)
        
        if trade_type.upper() == 'BUY':
            executed_price = requested_price + spread + slippage
        else:  # SELL
            executed_price = requested_price - spread - slippage
        
        return max(executed_price, 0.00001)  # Ensure positive price

    def get_risk_percentage(self):
        """Dynamic risk based on account performance"""
        pnl_perc = ((self.balance - self.initial_balance) / self.initial_balance) * 100
        if pnl_perc >= 6.0: 
            return 0.03
        elif pnl_perc >= 2.0: 
            return 0.01
        else: 
            return 0.005

    def open_trade(self, entry_time, entry_price, sl_price, trade_type, reason, context={}):
        """Open a new trade with realistic market friction"""
        # Apply market friction to entry
        executed_entry = self.apply_market_friction(entry_price, trade_type)
        
        risk_perc = self.get_risk_percentage()
        risk_amount = self.balance * risk_perc
        
        stop_loss_pips_val = abs(executed_entry - sl_price) / PIP_SIZE
        if stop_loss_pips_val == 0: 
            return

        calculated_lot_size = risk_amount / (stop_loss_pips_val * PIP_VALUE_PER_LOT)
        final_lot_size = min(calculated_lot_size, MAX_LOT_SIZE_CAP)

        # Calculate take profit levels
        tp_distance = (stop_loss_pips_val * PIP_SIZE) * 2  # 1:2 risk-reward
        partial_tp_distance = stop_loss_pips_val * PIP_SIZE  # 1:1 for partial
        
        if trade_type.upper() == 'BUY':
            tp_price = executed_entry + tp_distance
            partial_tp_price = executed_entry + partial_tp_distance
        else:  # SELL
            tp_price = executed_entry - tp_distance
            partial_tp_price = executed_entry - partial_tp_distance

        trade = {
            "entry_time": entry_time,
            "entry_price": executed_entry,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "partial_tp_price": partial_tp_price,
            "trade_type": trade_type.upper(),
            "reason": reason,
            "lot_size": final_lot_size,
            "original_lot_size": final_lot_size,
            "status": "OPEN",
            "partial_pnl": 0.0,
            "commission": final_lot_size * COMMISSION_PER_LOT,
        }
        trade.update(context)
        self.open_trades.append(trade)

    def check_open_trades(self, current_time, current_candle):
        """Check and manage open trades"""
        for trade in self.open_trades[:]:
            low_price, high_price = current_candle['low'], current_candle['high']

            if trade['status'] == 'OPEN':
                # Check for Stop Loss
                if (trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or \
                   (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price']):
                    self.close_trade(trade, current_time, trade['sl_price'], is_full_close=True)
                    continue

                # Check for Final Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price']):
                    self.close_trade(trade, current_time, trade['tp_price'], is_full_close=True)
                    continue

                # Check for Partial Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['partial_tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['partial_tp_price']):
                    self.handle_partial_close(trade, current_time)
                    continue

            elif trade['status'] == 'PARTIALLY_CLOSED':
                # Check for Stop Loss (now at breakeven)
                if (trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or \
                   (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price']):
                    self.close_trade(trade, current_time, trade['sl_price'], is_full_close=False)
                    continue
                
                # Check for Final Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price']):
                    self.close_trade(trade, current_time, trade['tp_price'], is_full_close=False)
                    continue

    def handle_partial_close(self, trade, current_time):
        """Handle partial position closing"""
        partial_lot_size = trade['original_lot_size'] / 2
        pnl_pips = abs(trade['partial_tp_price'] - trade['entry_price']) / PIP_SIZE
        pnl_amount = pnl_pips * PIP_VALUE_PER_LOT * partial_lot_size

        self.balance += pnl_amount
        trade['partial_pnl'] += pnl_amount
        trade['lot_size'] = partial_lot_size
        trade['sl_price'] = trade['entry_price']  # Move SL to breakeven
        trade['status'] = 'PARTIALLY_CLOSED'

    def close_trade(self, trade, exit_time, exit_price, is_full_close):
        """Close a trade and log results"""
        # Apply market friction to exit
        executed_exit = self.apply_market_friction(exit_price, 
                                                  'SELL' if trade['trade_type'] == 'BUY' else 'BUY')
        
        lot_size_to_close = trade['original_lot_size'] if is_full_close else trade['lot_size']
        
        pnl_pips = 0
        if trade['trade_type'] == 'BUY':
            pnl_pips = (executed_exit - trade['entry_price']) / PIP_SIZE
        else:  # SELL
            pnl_pips = (trade['entry_price'] - executed_exit) / PIP_SIZE
            
        final_pnl_part = pnl_pips * PIP_VALUE_PER_LOT * lot_size_to_close
        self.balance += final_pnl_part
        
        total_gross_pnl = trade['partial_pnl'] + final_pnl_part
        net_pnl = total_gross_pnl - trade['commission']

        # Update daily PnL
        self.daily_pnl += net_pnl
        
        log_entry = trade.copy()
        log_entry.update({
            "exit_time": exit_time,
            "exit_price": executed_exit,
            "net_pnl": net_pnl,
            "status": "CLOSED",
        })
        self.trade_log.append(log_entry)
        self.open_trades.remove(trade)
        
        return log_entry