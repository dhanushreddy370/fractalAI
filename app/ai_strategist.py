"""
The "Brain" - Stage 3: The Strategy Designer.

This agent acts as a world-class quantitative strategist. It now handles both
initial design and evolution, including implementing specific bug fixes.
Version: 2.2 - Updated prompt to handle bug fix instructions.
"""
import json
import os
import time
from openai import OpenAI, APITimeoutError

# --- Constants for API call resilience ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 180.0

def _call_llm_with_retry(client: OpenAI, model_name: str, messages: list, temperature: float) -> str:
    """Generic function to call the LLM with a retry mechanism."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            return response.choices[0].message.content
        except APITimeoutError:
            delay = RETRY_DELAY_SECONDS * (2**attempt)
            print(f"   - ⚠️ [Strategist] API call timed out. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Strategist] An unexpected API error occurred: {e}")
            return None
    print(f"   - ❌ [Strategist] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
    return None

def run(market_profile_path: str, version: int = 1) -> str:
    """
    Executes the initial AI strategy design process.
    """
    print("   - [Strategist] Loading config and Market Profile...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: config = json.load(f)
    with open(market_profile_path, 'r', encoding='utf-8') as f: market_profile = f.read()

    system_prompt = _get_strategist_prompt()
    user_prompt = f"Here is the Market Profile. Your task is to design a complete and robust scalping strategy based only on the statistical edges identified in this report.\n\n--- MARKET PROFILE ---\n{market_profile}\n--------------------"

    print(f"   - [Strategist] Sending profile to {config['model_name']} for strategy design (v{version})...")
    client = OpenAI(base_url=config['api_base_url'], api_key=config['api_key'])
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    strategy_document = _call_llm_with_retry(client, config['model_name'], messages, 0.2)
    
    if not strategy_document:
        return None

    report_dir = os.path.dirname(market_profile_path)
    base_filename = os.path.basename(report_dir)
    strategy_filename = f"{base_filename}_Scalping_Strategy_v{version}.txt"
    strategy_path = os.path.join(report_dir, strategy_filename)

    with open(strategy_path, 'w', encoding='utf-8') as f:
        f.write(strategy_document)
        
    return strategy_path

def run_optimization_cycle(previous_strategy_path: str, suggested_changes: list, version: int) -> str:
    """
    Executes an evolution of an existing strategy.
    """
    print("   - [Strategist] Evolving strategy based on AI feedback...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: config = json.load(f)
    with open(previous_strategy_path, 'r', encoding='utf-8') as f: previous_strategy = f.read()

    system_prompt = _get_strategist_prompt() # The core persona remains the same
    
    changes_str = "\n- ".join(suggested_changes)
    user_prompt = f"""
Your task is to evolve the following trading strategy based on the specific changes recommended by the AI analysis team.

--- PREVIOUS STRATEGY (Version {version-1}) ---
{previous_strategy}
-------------------------------------

--- REQUIRED CHANGES FOR NEXT VERSION ---
- {changes_str}
---------------------------------------

Please generate the complete, updated strategy document for Version {version}, incorporating ALL the required changes.
If the changes are for debugging, re-state the original strategy's logic but instruct the coder to implement the specific bug fix.
"""

    print(f"   - [Strategist] Sending v{version-1} and suggestions to {config['model_name']} for strategy evolution (v{version})...")
    client = OpenAI(base_url=config['api_base_url'], api_key=config['api_key'])
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    new_strategy_document = _call_llm_with_retry(client, config['model_name'], messages, 0.2)

    if not new_strategy_document:
        return None
    
    report_dir = os.path.dirname(previous_strategy_path)
    base_filename = os.path.basename(report_dir)
    new_strategy_filename = f"{base_filename}_Scalping_Strategy_v{version}.txt"
    new_strategy_path = os.path.join(report_dir, new_strategy_filename)

    with open(new_strategy_path, 'w', encoding='utf-8') as f:
        f.write(new_strategy_document)
        
    return new_strategy_path


def _get_strategist_prompt() -> str:
    """Contains the master instructions for the AI Strategist (OHLC-only, no indicators/order-flow)."""
    return """
You are 'AlgoSpec', a world-class quantitative strategist specializing in high-frequency scalping systems.

Absolute Constraints:
- Use ONLY OHLC-based price action concepts (candlesticks, structure, gaps, session behavior, support/resistance, liquidity sweeps defined via highs/lows).
- Do NOT use or mention technical indicators (RSI, MACD, Moving Averages, Bollinger, etc.).
- Do NOT use or mention volume or order-flow concepts.

Your Task:
You will be given either a 'Market Profile' to design a new strategy, or a previous strategy document and a list of required changes. Your mission is to produce a single, complete, and robust strategy document.

CRITICAL INSTRUCTIONS:
1. Handle Your Input:
   - If given a Market Profile, every rule in your new strategy must be justified by a specific statistic from that report (all OHLC-derived).
   - If given a list of changes, you must meticulously incorporate every change into the new version of the strategy document.
2. Clarity is Key: Your output must always be a clean, formal strategy document. Do not add conversational text. The AI Coder will read this document directly.
3. KPIs: Define how to calculate key performance metrics (e.g., Profit Factor, win rate, max drawdown) in a backtest context without indicators.

Strategy Document Structure:
- 1. Strategy Name & Core Concept
- 2. Market & Timeframe
- 3. Statistical Foundation (OHLC-only evidence)
- 4. Entry Rules (pure price action)
- 5. Exit Rules (TP/SL and management, pure price-based)
- 6. Risk Management (position sizing rules, daily risk caps)
- 7. Key Performance Metrics (how to compute in backtests)
- 8. (If applicable) Coder Instructions (explicit implementation notes)
"""
