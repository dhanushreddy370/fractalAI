# EUR/USD Momentum Scalper Backtester

A high-frequency scalping strategy designed to exploit EUR/USD's tendency for efficient directional moves at key structural levels using pure OHLC price action.

## Strategy Overview

- **Market:** EUR/USD
- **Primary Timeframe:** M15 for entry/exit execution
- **Key Features:** Momentum break entries and liquidity sweep fade entries
- **Risk Management:** 0.5% risk per trade, 2% daily loss cap, max 10 trades/day

## Installation

```bash
pip install matplotlib pandas numpy
```

## Usage

```bash
python backtester.py path_to_your_data.csv
```

Replace `path_to_your_data.csv` with your 1-minute EUR/USD OHLC data file.

## Data Format

CSV file must contain columns: `time`, `open`, `high`, `low`, `close`, and either `real_volume` or `tick_volume`.

## Output

Results are saved to the `results/` directory, including:
- Performance report with key metrics
- Equity curve visualization
- Trade log with detailed analysis
- Stop-loss distribution charts