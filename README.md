# FractalAI: Autonomous Forex Analysis & Strategy Generation

FractalAI is a sophisticated, multi-agent AI system that performs end-to-end analysis of forex market data. It operates on pure OHLC (Open, High, Low, Close) data to autonomously discover behavioral patterns, design trading strategies, generate backtesting code, and iteratively optimize them.

**Core Philosophy:** No technical indicators, no volume, no order flow. FractalAI's edge comes from a deep, multi-faceted analysis of pure price action.

---

## 🚀 Features

- **Multi-Agent System:** A team of specialized AI agents work together, each focusing on a different aspect of market analysis (market structure, candlestick patterns, session behavior, etc.).
- **End-to-End Automation:** From raw M1 data to a fully coded and optimized trading strategy, the entire workflow is automated.
- **Pure Price Action:** Strategies are based on observable price patterns, not lagging indicators.
- **Iterative Optimization:** The system designs, tests, and then improves its own strategies based on backtest performance.
- **Full Transparency:** Generates detailed reports at every stage of the analysis and optimization process.

---

## 📊 Workflow Overview

1.  **Quantitative Engine:** Ingests M1 OHLC data and performs a deep statistical analysis of price behavior.
2.  **AI Analysis Team:** A team of 5 specialized AI agents (Analyst, Structure, Candles, Sessions, S/R) dissects the quantitative data.
3.  **AI Strategist:** Synthesizes the reports from the analysis team to design a novel, pure price-action trading strategy.
4.  **AI Coder:** Writes a complete Python backtesting project for the designed strategy.
5.  **Backtesting & Optimization:** The strategy is automatically backtested. An AI Optimizer or Debugger analyzes the results, suggests improvements, and kicks off the next optimization cycle.

This loop continues until the AI determines the strategy is optimal or the maximum number of cycles is reached.

---

## Usage

1.  **Place your data:** Put your M1 OHLC data (in `.csv` format) into the `input/` directory.
2.  **Run the analysis:**
    ```bash
    python run_analysis.py
    ```
    The script will prompt you to enter the path to your data file.

The final, optimized strategy code and detailed performance reports will be saved in the `analysis_results/` directory.

---
