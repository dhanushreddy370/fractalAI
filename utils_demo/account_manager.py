import pandas as pd
import numpy as np

"""
Upgraded Account Manager (with Partial Profits)

This is a heavily upgraded version of the account manager.
NEW FEATURES:
- Partial Profit Taking: Automatically closes half the position at 1:1 R:R.
- Move to Breakeven: Moves the SL to the entry price after taking partials.
- Consolidated P/L: The trade log shows the final combined P/L for each trade.
"""

# --- Configuration for costs ---
COMMISSION_PER_LOT = 3.5
PIP_VALUE_PER_LOT = 10.0
PIP_SIZE = 0.0001
MAX_LOT_SIZE_CAP = 500.0

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

    def open_trade(self, entry_time, entry_price, sl_price, trade_type, reason, context={}, tp_price=None):
        risk_perc = self.get_risk_percentage()
        risk_amount = self.balance * risk_perc
        
        stop_loss_pips_val = abs(entry_price - sl_price) / PIP_SIZE
        if stop_loss_pips_val == 0: return

        calculated_lot_size = risk_amount / (stop_loss_pips_val * PIP_VALUE_PER_LOT)
        final_lot_size = min(calculated_lot_size, MAX_LOT_SIZE_CAP)

        # Calculate final TP if not provided
        if tp_price is None:
            tp_distance = (stop_loss_pips_val * PIP_SIZE) * self.risk_to_reward
            tp_price = entry_price + tp_distance if trade_type.upper() == 'BUY' else entry_price - tp_distance

        # NEW: Calculate the partial take profit level (at 1:1 Risk/Reward)
        partial_tp_distance = stop_loss_pips_val * PIP_SIZE
        partial_tp_price = entry_price + partial_tp_distance if trade_type.upper() == 'BUY' else entry_price - partial_tp_distance

        trade = {
            "entry_time": entry_time,
            "entry_price": entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "partial_tp_price": partial_tp_price, # New field
            "trade_type": trade_type.upper(),
            "reason": reason,
            "lot_size": final_lot_size,
            "original_lot_size": final_lot_size, # New field to store initial size
            "status": "OPEN", # New field: OPEN, PARTIALLY_CLOSED
            "partial_pnl": 0.0, # New field to accumulate P/L
            "commission": final_lot_size * COMMISSION_PER_LOT, # Calculate commission upfront
        }
        trade.update(context)
        self.open_trades.append(trade)

    def check_open_trades(self, current_time, current_candle):
        closed_trade_log = None
        for trade in self.open_trades[:]: # Iterate over a copy
            low_price, high_price = current_candle['low'], current_candle['high']

            # --- Logic for fully open trades ---
            if trade['status'] == 'OPEN':
                # 1. Check for Stop Loss
                if (trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or \
                   (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['sl_price'], is_full_close=True)
                    continue

                # 2. Check for Final Take Profit (hit before partial)
                if (trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['tp_price'], is_full_close=True)
                    continue

                # 3. Check for Partial Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['partial_tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['partial_tp_price']):
                    self.handle_partial_close(trade, current_time)
                    # The trade remains in open_trades, but its state is changed.
                    continue

            # --- Logic for partially closed trades ---
            elif trade['status'] == 'PARTIALLY_CLOSED':
                # 1. Check for Stop Loss (now at breakeven)
                if (trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or \
                   (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['sl_price'], is_full_close=False)
                    continue
                
                # 2. Check for Final Take Profit
                if (trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or \
                   (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price']):
                    closed_trade_log = self.close_trade(trade, current_time, trade['tp_price'], is_full_close=False)
                    continue
        
        return closed_trade_log

    def handle_partial_close(self, trade, current_time):
        """NEW: Handles the logic for closing half the position."""
        # Calculate P/L for half the position
        partial_lot_size = trade['original_lot_size'] / 2
        pnl_pips = abs(trade['partial_tp_price'] - trade['entry_price']) / PIP_SIZE
        pnl_amount = pnl_pips * PIP_VALUE_PER_LOT * partial_lot_size

        # Update account balance and trade's internal P/L
        self.balance += pnl_amount
        trade['partial_pnl'] += pnl_amount
        
        # Update trade state
        trade['lot_size'] = partial_lot_size # Reduce lot size for remaining position
        trade['sl_price'] = trade['entry_price'] # Move SL to Break-even
        trade['status'] = 'PARTIALLY_CLOSED'
        
        # Log this event for potential debugging, but not to the final trade log
        # print(f"{current_time}: Partial profit taken for trade entered at {trade['entry_time']}. P/L: ${pnl_amount:.2f}")

    def close_trade(self, trade, exit_time, exit_price, is_full_close):
        """Closes a trade (or the remainder of it) and logs it."""
        
        # Determine the lot size being closed now
        lot_size_to_close = trade['original_lot_size'] if is_full_close else trade['lot_size']
        
        # Calculate P/L for this closing portion
        pnl_pips = 0
        if trade['trade_type'] == 'BUY':
            pnl_pips = (exit_price - trade['entry_price']) / PIP_SIZE
        else: # SELL
            pnl_pips = (trade['entry_price'] - exit_price) / PIP_SIZE
            
        final_pnl_part = pnl_pips * PIP_VALUE_PER_LOT * lot_size_to_close

        # Update balance with the P/L from this final part
        self.balance += final_pnl_part
        
        # The total net P/L for the log is the sum of the partial and final parts
        total_gross_pnl = trade['partial_pnl'] + final_pnl_part
        # Subtract the commission that was calculated upfront for the whole trade
        net_pnl = total_gross_pnl - trade['commission']

        # Create the log entry
        log_entry = trade.copy()
        log_entry.update({
            "exit_time": exit_time,
            "exit_price": exit_price,
            "net_pnl": net_pnl, # The final, consolidated P/L
            "status": "CLOSED",
        })
        self.trade_log.append(log_entry)
        self.open_trades.remove(trade)
        return log_entry
