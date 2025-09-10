import pandas as pd
import numpy as np

# Configuration for costs and market friction
COMMISSION_PER_LOT = 3.5
PIP_VALUE_PER_LOT = 10.0
PIP_SIZE = 0.0001
MAX_LOT_SIZE_CAP = 500.0
BASE_SPREAD = 0.00005  # 0.5 pips base spread
SPREAD_VARIABILITY = 0.00002  # Additional random spread component
SLIPPAGE = 0.00003  # Average slippage per trade

class TradingAccount:
    def __init__(self, initial_balance=10000.0, risk_to_reward=2.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.risk_to_reward = risk_to_reward
        self.open_trades = []
        self.trade_log = []

    def get_pnl_percentage(self):
        return ((self.balance - self.initial_balance) / self.initial_balance) * 100

    def get_risk_percentage(self):
        pnl_perc = self.get_pnl_percentage()
        if pnl_perc >= 6.0: return 0.03
        elif pnl_perc >= 2.0: return 0.01
        else: return 0.005

    def apply_market_friction(self, requested_price, trade_type):
        """Apply spread and slippage to requested price"""
        spread = BASE_SPREAD + np.random.random() * SPREAD_VARIABILITY
        slippage = np.random.normal(SLIPPAGE, SLIPPAGE/2)
        
        if trade_type.upper() == 'BUY':
            return requested_price + spread + slippage
        else:  # SELL
            return requested_price - spread - slippage

    def open_trade(self, entry_time, entry_price, sl_price, trade_type, reason, context={}, tp_price=None):
        risk_perc = self.get_risk_percentage()
        risk_amount = self.balance * risk_perc
        
        # Apply market friction to entry price
        actual_entry_price = self.apply_market_friction(entry_price, trade_type)
        
        stop_loss_pips_val = abs(actual_entry_price - sl_price) / PIP_SIZE
        if stop_loss_pips_val == 0: return

        calculated_lot_size = risk_amount / (stop_loss_pips_val * PIP_VALUE_PER_LOT)
        final_lot_size = min(calculated_lot_size, MAX_LOT_SIZE_CAP)

        # Calculate final TP if not provided
        if tp_price is None:
            tp_distance = (stop_loss_pips_val * PIP_SIZE) * self.risk_to_reward
            tp_price = actual_entry_price + tp_distance if trade_type.upper() == 'BUY' else actual_entry_price - tp_distance

        # Calculate partial take profit level (at 1:1 Risk/Reward)
        partial_tp_distance = stop_loss_pips_val * PIP_SIZE
        partial_tp_price = actual_entry_price + partial_tp_distance if trade_type.upper() == 'BUY' else actual_entry_price - partial_tp_distance

        trade = {
            "entry_time": entry_time,
            "entry_price": actual_entry_price,
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
        closed_trade_log = None
        for trade in self.open_trades[:]:
            low_price, high_price = current_candle['low'], current_candle['high']

            # Logic for fully open trades
            if trade['status'] == 'OPEN':
                # Check for Stop Loss
                if (trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or \
                   (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['sl_price'], is_full_close=True)
                    continue

                # Check for Final Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['tp_price'], is_full_close=True)
                    continue

                # Check for Partial Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['partial_tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['partial_tp_price']):
                    self.handle_partial_close(trade, current_time)
                    continue

            # Logic for partially closed trades
            elif trade['status'] == 'PARTIALLY_CLOSED':
                # Check for Stop Loss (now at breakeven)
                if (trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or \
                   (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['sl_price'], is_full_close=False)
                    continue
                
                # Check for Final Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['tp_price'], is_full_close=False)
                    continue
        
        return closed_trade_log

    def handle_partial_close(self, trade, current_time):
        """Handles the logic for closing half the position."""
        partial_lot_size = trade['original_lot_size'] / 2
        pnl_pips = abs(trade['partial_tp_price'] - trade['entry_price']) / PIP_SIZE
        pnl_amount = pnl_pips * PIP_VALUE_PER_LOT * partial_lot_size

        self.balance += pnl_amount
        trade['partial_pnl'] += pnl_amount
        
        trade['lot_size'] = partial_lot_size
        trade['sl_price'] = trade['entry_price']
        trade['status'] = 'PARTIALLY_CLOSED'

    def close_trade(self, trade, exit_time, exit_price, is_full_close):
        """Closes a trade (or the remainder of it) and logs it."""
        
        lot_size_to_close = trade['original_lot_size'] if is_full_close else trade['lot_size']
        
        pnl_pips = 0
        if trade['trade_type'] == 'BUY':
            pnl_pips = (exit_price - trade['entry_price']) / PIP_SIZE
        else: # SELL
            pnl_pips = (trade['entry_price'] - exit_price) / PIP_SIZE
            
        final_pnl_part = pnl_pips * PIP_VALUE_PER_LOT * lot_size_to_close

        self.balance += final_pnl_part
        
        total_gross_pnl = trade['partial_pnl'] + final_pnl_part
        net_pnl = total_gross_pnl - trade['commission']

        log_entry = trade.copy()
        log_entry.update({
            "exit_time": exit_time,
            "exit_price": exit_price,
            "net_pnl": net_pnl,
            "status": "CLOSED",
        })
        self.trade_log.append(log_entry)
        self.open_trades.remove(trade)
        return log_entry