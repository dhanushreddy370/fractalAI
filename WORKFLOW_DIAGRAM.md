# FractalAI v3.0 - Enhanced Pure OHLC Price Action Workflow

## 🚀 **SYSTEM OVERVIEW**
FractalAI is now a **Pure OHLC Price Action Analysis Suite** that uses multiple specialized AI agents to autonomously analyze forex market data, design strategies, code them, and iteratively optimize them - all using **ONLY** Open, High, Low, Close data.

**Key Philosophy: NO technical indicators, NO volume data, NO order flow - Pure price behavior analysis only.**

---

## 📊 **COMPLETE WORKFLOW DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                               FRACTAL AI v3.0 - WORKFLOW                                │
│                          Pure OHLC Price Action Analysis Suite                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌───────────────────────────────────────────────────────────────────┐
│  INPUT DATA     │    │                     STAGE 1: QUANTITATIVE ENGINE                  │
│                 │────▶                        (Pure OHLC Analysis)                       │
│ • M1 OHLC CSV   │    │                                                                   │
│ • Time, O,H,L,C │    │ ┌─────────────────┬─────────────────┬─────────────────────────┐   │
│ • No Volume     │    │ │ Multi-Timeframe │ Session Analysis│ Key Level Reactions     │   │
│ • No Indicators │    │ │ • M15/H1/H4/D/W │ • Asian/London/ │ • Session H/L           │   │
│                 │    │ │ • Market Struct │   NY behavior   │ • HTF Highs/Lows        │   │
└─────────────────┘    │ │ • Path Dynamics │ • DST-aware     │ • Liquidity Sweeps      │   │
                       │ └─────────────────┴─────────────────┴─────────────────────────┘   │
                       │                                                                   │
                       │ OUTPUT: quantitative_output.json (Pure OHLC statistics)           │
                       └─────────────────────────┬─────────────────────────────────────────┘
                                                 │
                       ┌─────────────────────────▼─────────────────────────────────────────┐
                       │                  STAGE 2: AI ANALYSIS TEAM                        │
                       │                   (5 Specialized AI Agents)                       │
                       │                                                                   │
                       │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
                       │ │2a: ANALYST  │ │2b: STRUCTURE│ │2c: CANDLES  │ │2d: SESSIONS │   │
                       │ │             │ │             │ │             │ │             │   │
                       │ │ Market      │ │ Higher H/L  │ │ Doji, Pin   │ │ Asian/LDN   │   │
                       │ │ Profile     │ │ Structure   │ │ Engulfing   │ │ NY behavior │   │
                       │ │ Overview    │ │ Breaks      │ │ Patterns    │ │ Gap analysis│   │
                       │ │             │ │ S/R Levels  │ │ Reliability │ │ Ranges      │   │
                       │ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
                       │                                                                   │
                       │ ┌─────────────┐                                                   │
                       │ │2e: S/R      │     Each Agent Produces Specialized Report        │
                       │ │             │                                                   │
                       │ │ Support     │     • Market_Profile.txt                          │
                       │ │ Resistance  │     • Market_Structure_Analysis.txt               │
                       │ │ Level       │     • Candlestick_Pattern_Analysis.txt            │
                       │ │ Analysis    │     • Session_Behavior_Analysis.txt               │
                       │ │             │     • Support_Resistance_Analysis.txt             │
                       │ └─────────────┘                                                   │
                       └─────────────────────────┬─────────────────────────────────────────┘
                                                 │
                       ┌─────────────────────────▼─────────────────────────────────────────┐
                       │                STAGE 3: AI STRATEGIST                             │
                       │              (Pure Price Action Strategy Design)                  │
                       │                                                                   │
                       │ Uses Market Profile + All Analysis Reports to Design:             │
                       │                                                                   │
                       │ ┌─────────────────────────────────────────────────────────────┐   │
                       │ │ PURE OHLC STRATEGIES:                                       │   │
                       │ │ • Structure-based (HH/LL breaks)                            │   │
                       │ │ • Level-based (S/R bounces/breaks)                          │   │
                       │ │ • Pattern-based (Candlestick formations)                    │   │
                       │ │ • Session-based (Time-specific behavior)                    │   │
                       │ │ • Gap-based (Opening gaps, fills)                           │   │
                       │ └─────────────────────────────────────────────────────────────┘   │
                       │                                                                   │
                       │ OUTPUT: Strategy_v1.txt (Complete trading rules)                  │
                       └─────────────────────────┬─────────────────────────────────────────┘
                                                 │
                       ┌─────────────────────────▼─────────────────────────────────────────┐
                       │                   STAGE 4: AI CODER                               │
                       │                (OHLC-Only Code Generation)                        │
                       │                                                                   │
                       │ Generates Complete Python Project:                                │
                       │                                                                   │
                       │ ┌─────────────────────────────────────────────────────────────┐   │
                       │ │ FILES CREATED:                                              │   │
                       │ │ • backtester.py (Main execution)                            │   │
                       │ │ • utils/data_handler.py (OHLC processing)                   │   │
                       │ │ • utils/pattern_engine.py (OHLC patterns)                   │   │
                       │ │ • utils/account_manager.py (Trade simulation)               │   │
                       │ │ • utils/reporting.py (Results & charts)                     │   │
                       │ │ • README.md (Documentation)                                 │   │
                       │ └─────────────────────────────────────────────────────────────┘   │
                       │                                                                   │
                       │ CONSTRAINTS ENFORCED:                                             │
                       │ • NO technical indicator libraries                                │
                       │ • NO volume-based calculations                                    │
                       │ • Pure OHLC pattern recognition only                              │
                       └─────────────────────────┬─────────────────────────────────────────┘
                                                 │
                       ┌─────────────────────────▼─────────────────────────────────────────┐
                       │                 STAGE 5: BACKTESTING                              │
                       │               (Automated Strategy Execution)                      │
                       │                                                                   │
                       │ ┌─────────────────────────────────────────────────────────────┐   │
                       │ │ BACKTEST EXECUTION:                                         │   │
                       │ │ • Load M1 OHLC data                                         │   │
                       │ │ • Apply pure price action rules                             │   │
                       │ │ • Simulate realistic spreads & slippage                     │   │
                       │ │ • Generate trade log & performance metrics                  │   │
                       │ └─────────────────────────────────────────────────────────────┘   │
                       │                                                                   │
                       │ OUTPUTS:                                                          │
                       │ • strategy_vX_report.txt                                          │
                       │ • strategy_vX_trade_log.csv                                       │
                       └─────────────────────────┬─────────────────────────────────────────┘
                                                 │
                                                 ▼
                       ┌─────────────────────────────────────────────────────────────────┐
                       │                 STAGE 6: AI OPTIMIZATION                        │
                       │                                                                 │
                       │     ┌─────────────────┐    OR    ┌─────────────────────────────┐│
                       │     │ 6a: DEBUGGER    │          │ 6b: OPTIMIZER               ││
                       │     │                 │          │                             ││
                       │     │ IF CRASH:       │          │ IF SUCCESS:                 ││
                       │     │ • Analyze error │          │ • Analyze performance       ││
                       │     │ • Fix code bugs │          │ • Suggest improvements      ││
                       │     │ • Return fixes  │          │ • Enhance strategy rules    ││
                       │     └─────────────────┘          └─────────────────────────────┘│
                       │                                                                 │
                       │ OUTPUT: Suggested changes for next version                      │
                       └─────────────────────────┬───────────────────────────────────────┘
                                                 │
                                    ┌────────────▼─────────────┐
                                    │   ITERATIVE LOOP        │
                                    │                         │
                                    │ Max 5 optimization      │
                                    │ cycles or until AI      │
                                    │ declares "OPTIMAL"      │
                                    │                         │
                                    │ Each cycle creates      │
                                    │ improved strategy vX+1  │
                                    └─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                FINAL OUTPUTS                                            │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ analysis_results/SYMBOL/                                                                │
│ ├── reports/                                                                            │
│ │   ├── Market_Profile.txt                    (Main market analysis)                    │
│ │   ├── Market_Structure_Analysis.txt         (HH/LL, structure breaks)                 │
│ │   ├── Candlestick_Pattern_Analysis.txt      (Pattern reliability & context)           │
│ │   ├── Session_Behavior_Analysis.txt         (Time-based price behavior)               │
│ │   ├── Support_Resistance_Analysis.txt       (Key levels & reactions)                  │
│ │   ├── SYMBOL_Scalping_Strategy_vX.txt       (Final optimized strategy)                │
│ │   └── Version_Control_Report.md             (Optimization history)                    │
│ └── strategies/                                                                         │
│     └── vX/                                   (Final version folder)                    │
│         ├── backtester.py                     (Runnable strategy code)                  │
│         ├── utils/                                                                      │
│         │   ├── data_handler.py               (OHLC data processing)                    │
│         │   ├── pattern_engine.py             (Pure price action logic)                 │
│         │   ├── account_manager.py            (Trade simulation)                        │
│         │   └── reporting.py                  (Results generation)                      │
│         └── results/                                                                    │
│             ├── strategy_vX_report.txt        (Performance metrics)                     │
│             └── strategy_vX_trade_log.csv     (Detailed trade history)                  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 **KEY SYSTEM CONSTRAINTS (PURE OHLC ONLY)**

### ✅ **ALLOWED DATA & ANALYSIS:**
- **OHLC Time Series**: Open, High, Low, Close, Timestamp
- **Candlestick Patterns**: Doji, hammer, engulfing, pin bars, etc.
- **Market Structure**: Higher highs, lower lows, structure breaks
- **Support/Resistance**: Historical price levels from OHLC
- **Session Analysis**: Time-based price behavior patterns
- **Gap Analysis**: Price gaps between sessions
- **Range Analysis**: Daily/session ranges from H-L
- **Price Efficiency**: How price moves between levels

### ❌ **STRICTLY FORBIDDEN:**
- **Technical Indicators**: RSI, MACD, Moving Averages, Bollinger Bands, etc.
- **Volume Analysis**: Any volume-based calculations or patterns
- **Order Flow**: Bid/ask, market depth, time & sales
- **Derived Indicators**: ATR, momentum oscillators, etc.
- **External Data**: Economic news, sentiment, COT reports

---

## 🧠 **AI AGENT SPECIALIZATIONS**

### **1. Quantitative Engine** 🔢
- Pure OHLC statistical analysis
- Multi-timeframe resampling (M15, H1, H4, D1, W1)
- Session-based calculations (Asian, London, NY)
- Key level interaction analysis (proximity via candle ranges)

### **2a. AI Analyst** 🧠
- Main market profiler and behavioral interpreter
- Synthesizes quantitative data into readable insights
- Focuses on scalping-relevant anomalies

### **2b. Market Structure Analyzer** 📊
- Higher high/lower low pattern detection
- Structure break identification
- Multi-timeframe structure alignment
- Trend vs range classification

### **2c. Candlestick Pattern Expert** 🕯️
- Single & multi-candle pattern recognition
- Pattern reliability assessment
- Context-dependent pattern analysis
- Session-specific pattern behavior

### **2d. Session Behavior Specialist** ⏰
- Time-based price behavior analysis
- Gap pattern identification
- Intraday range dynamics
- Session transition analysis

### **2e. Support/Resistance Expert** 📈
- Historical level identification
- Level strength assessment
- Reaction pattern analysis (bounces, breaks, sweeps)
- Multi-timeframe level confluence

### **3. AI Strategist** 💡
- Pure price action strategy design
- Multi-report synthesis for strategy rules
- Risk management framework creation
- Performance metric definition

### **4. AI Coder** 💻
- OHLC-only code generation
- Complete backtesting project creation
- Realistic market simulation
- No indicator dependencies enforced

### **5. AI Optimizer/Debugger** 🔧
- Performance analysis and enhancement
- Bug identification and fixing
- Strategy evolution guidance
- Robustness assessment

---

## 📈 **STRATEGY TYPES GENERATED**

Based on pure OHLC analysis, the system can generate:

1. **Structure-Based Strategies**: Trading market structure breaks and continuations
2. **Level-Based Strategies**: Support/resistance bounces and breakouts
3. **Pattern-Based Strategies**: Candlestick formation trading
4. **Session-Based Strategies**: Time-specific behavior exploitation
5. **Gap-Based Strategies**: Opening gap fills and continuations
6. **Range-Based Strategies**: Breakout and mean reversion systems

---

## 🎯 **SYSTEM BENEFITS**

- **Pure Price Action Focus**: No indicator lag or false signals
- **Robust Analysis**: Multiple specialized AI perspectives
- **Automated Workflow**: End-to-end strategy development
- **Iterative Improvement**: Self-optimizing system
- **Realistic Testing**: Market friction simulation
- **Complete Documentation**: Full audit trail of decisions

---

## 🚀 **USAGE EXAMPLE**
- Store your data in the input folder
- Navigate to the repository root and run:
```bash
python run_analysis.py "input/EURUSD_M1.csv"
```

The system will:
1. ✅ Analyze the OHLC data with 5 AI agents
2. ✅ Design a pure price action strategy
3. ✅ Code the complete backtesting system
4. ✅ Run automated backtests
5. ✅ Optimize through multiple iterations
6. ✅ Deliver final optimized strategy ready for deployment

**Result**: A complete, tested, pure price action trading system based entirely on OHLC behavioral patterns.
