import pandas as pd
import numpy as np

"""
Account Manager for EUR/USD Momentum Scalper with realistic market friction
"""

# --- Configuration for costs ---
COMMISSION_PER_LOT = 3.5
PIP_VALUE_PER_LOT = 10.0
PIP_SIZE = 0.0001
MAX_LOT_SIZE_CAP = 500.0

class TradingAccount:
    def __init__(self, initial_balance=10000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.open_trades = []
        self.trade_log = []
        self.daily_trades = []

    def apply_market_friction(self, price, trade_type):
        """Apply variable spread and slippage"""
        # Variable spread: 0.5 pips base + random component
        spread = PIP_SIZE * (0.5 + np.random.random() * 0.2)
        
        # Slippage: random 0-1 pip
        slippage = PIP_SIZE * np.random.random()
        
        if trade_type.upper() == 'BUY':
            return price + spread + slippage
        else:
            return price - spread - slippage

    def get_risk_amount(self):
        """Risk 0.5% of capital per trade"""
        return self.balance * 0.005

    def open_trade(self, entry_time, entry_price, sl_price, trade_type, reason, context={}, tp_price=None):
        """Open a new trade with market friction"""
        # Apply market friction to entry price
        actual_entry_price = self.apply_market_friction(entry_price, trade_type)
        
        risk_amount = self.get_risk_amount()
        
        stop_loss_pips_val = abs(actual_entry_price - sl_price) / PIP_SIZE
        if stop_loss_pips_val == 0:
            return

        calculated_lot_size = risk_amount / (stop_loss_pips_val * PIP_VALUE_PER_LOT)
        final_lot_size = min(calculated_lot_size, MAX_LOT_SIZE_CAP)

        # Calculate final TP if not provided
        if tp_price is None:
            tp_distance = stop_loss_pips_val * PIP_SIZE * 2  # 1:2 risk-reward
            tp_price = actual_entry_price + tp_distance if trade_type.upper() == 'BUY' else actual_entry_price - tp_distance

        trade = {
            "entry_time": entry_time,
            "entry_price": actual_entry_price,
            "sl_price": sl_price,
            "tp_price": tp_price,
            "trade_type": trade_type.upper(),
            "reason": reason,
            "lot_size": final_lot_size,
            "commission": final_lot_size * COMMISSION_PER_LOT,
            "status": "OPEN",
        }
        trade.update(context)
        self.open_trades.append(trade)

    def check_open_trades(self, current_time, current_candle):
        """Check if any open trades should be closed"""
        closed_trade_log = None
        
        for trade in self.open_trades[:]:
            low_price, high_price = current_candle['low'], current_candle['high']

            # Check for Stop Loss
            if ((trade['trade_type'] == 'BUY' and low_price <= trade['sl_price']) or
                (trade['trade_type'] == 'SELL' and high_price >= trade['sl_price'])):
                
                closed_trade_log = self.close_trade(trade, current_time, trade['sl_price'], True)
                continue

            # Check for Take Profit
            if ((trade['trade_type'] == 'BUY' and high_price >= trade['tp_price']) or
                (trade['trade_type'] == 'SELL' and low_price <= trade['tp_price'])):
                
                closed_trade_log = self.close_trade(trade, current_time, trade['tp_price'], True)
                continue
        
        return closed_trade_log

    def close_trade(self, trade, exit_time, exit_price, is_full_close):
        """Close a trade and calculate P&L"""
        # Apply market friction to exit price
        actual_exit_price = self.apply_market_friction(exit_price, 
                                                     'SELL' if trade['trade_type'] == 'BUY' else 'BUY')
        
        # Calculate P&L
        if trade['trade_type'] == 'BUY':
            pnl_pips = (actual_exit_price - trade['entry_price']) / PIP_SIZE
        else:
            pnl_pips = (trade['entry_price'] - actual_exit_price) / PIP_SIZE
            
        pnl_amount = pnl_pips * PIP_VALUE_PER_LOT * trade['lot_size']
        net_pnl = pnl_amount - trade['commission']

        # Update balance
        self.balance += net_pnl

        # Create log entry
        log_entry = trade.copy()
        log_entry.update({
            "exit_time": exit_time,
            "exit_price": actual_exit_price,
            "net_pnl": net_pnl,
            "status": "CLOSED",
        })
        
        self.trade_log.append(log_entry)
        self.open_trades.remove(trade)
        
        return log_entry

    def get_daily_stats(self):
        """Get daily trading statistics"""
        if not self.trade_log:
            return {"trades": 0, "pnl": 0}
        
        df = pd.DataFrame(self.trade_log)
        df['exit_date'] = pd.to_datetime(df['exit_time']).dt.date
        
        daily_stats = df.groupby('exit_date').agg({
            'net_pnl': 'sum',
            'reason': 'count'
        }).rename(columns={'reason': 'trades'})
        
        return daily_stats