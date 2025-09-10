# EUR/USD Momentum Scalper Backtester

A high-frequency scalping strategy designed to exploit EUR/USD's tendency for efficient directional moves at key structural levels using pure OHLC price action.

## Strategy Overview

- **Market:** EUR/USD
- **Primary Timeframe:** M15 for entry/exit execution
- **Key Features:** Momentum break entries and liquidity sweep fades
- **Risk Management:** 0.5% risk per trade, 2% daily loss cap
- **Pure Price Action:** No technical indicators used

## How to Run

1. Place your 1-minute EUR/USD CSV data file in the project directory
2. Run from command line:
   ```
   python backtester.py path_to_your_data.csv
   ```
3. Results will be saved in the `results/` directory

## Required Data Format

CSV file with columns: `time`, `open`, `high`, `low`, `close`, and either `real_volume` or `tick_volume`

## Key Performance Metrics

- Profit Factor
- Win Rate
- Max Drawdown
- Average Trade Duration
- Key Level Performance Analysis