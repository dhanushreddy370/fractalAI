# EUR/USD Momentum Scalper Backtester

A high-frequency scalping strategy for EUR/USD that exploits momentum breaks at key structural levels using pure OHLC price action.

## Strategy Overview

- **Market**: EUR/USD
- **Primary Timeframe**: M15 for entry/exit execution
- **Key Levels**: Previous daily/weekly/session highs/lows
- **Entry Types**: Momentum breaks and liquidity sweep fades
- **Risk Management**: 0.5% risk per trade, 2% daily loss cap

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python backtester.py path_to_your_data.csv
```

## Data Format

CSV file must contain: `time, open, high, low, close, volume` columns with 1-minute data.

## Results

All results are saved to the `results/` directory including:
- Performance reports
- Equity curve charts
- Trade logs
- Forensic analysis