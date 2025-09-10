# EUR/USD Momentum Scalper Backtester

A high-frequency scalping strategy designed to exploit EUR/USD's tendency for efficient directional moves at key structural levels using pure OHLC price action.

## Strategy Overview

- **Market:** EUR/USD
- **Primary Timeframe:** M15 for entry/exit execution
- **Analysis Timeframes:** H1, H4, Daily for key level identification
- **Core Concept:** Enter on confirmed momentum breaks at key levels with high probability of liquidity sweeps and breach-and-continue scenarios

## Key Features

- Pure OHLC price action (no indicators, no volume-based logic)
- Realistic market friction modeling (spread + slippage)
- Comprehensive performance reporting
- Key level performance tracking
- Daily risk management constraints

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python backtester.py path_to_your_data.csv
```

Replace `path_to_your_data.csv` with your 1-minute EUR/USD OHLC data file.

## Data Format

Your CSV file should contain the following columns:
- `time`: datetime in UTC format
- `open`: open price
- `high`: high price
- `low`: low price
- `close`: close price
- `volume`: volume data (optional)

## Output

Results are saved to the `results/` directory, including:
- Performance report with key metrics
- Equity curve visualization
- Trade log with detailed entries/exits
- Key level performance analysis