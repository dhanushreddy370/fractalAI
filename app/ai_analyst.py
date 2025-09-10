"""
The "Brain" - Stage 2: The Market Profiler.

This module uses an LLM to interpret the quantitative data and generate
an objective, factual Market Profile report, highlighting scalping edges.
v2.2 - Added robust retry mechanism for API calls.
"""
import json
import os
import time
from openai import OpenAI, APITimeoutError

# --- Constants for API call resilience ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 180.0

def run(quantitative_output_path: str) -> str:
    """Executes the AI analysis and Market Profile generation."""
    print("   - [Analyst] Loading config and quantitative data...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: config = json.load(f)
    with open(quantitative_output_path, 'r') as f: quantitative_data = json.load(f)

    system_prompt = _get_market_profiler_prompt()
    user_prompt = f"Here is the quantitative analysis data. Generate the Market Profile based on your instructions.\n\nDATA:\n{json.dumps(quantitative_data, indent=2)}"

    print(f"   - [Analyst] Sending data to {config['model_name']} for profiling...")
    
    report_content = None
    for attempt in range(MAX_RETRIES):
        try:
            client = OpenAI(base_url=config['api_base_url'], api_key=config['api_key'])
            response = client.chat.completions.create(
                model=config['model_name'],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            report_content = response.choices[0].message.content
            break # Success, exit retry loop
        except APITimeoutError:
            delay = RETRY_DELAY_SECONDS * (2**attempt)
            print(f"   - ⚠️ [Analyst] API call timed out. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Analyst] An unexpected API error occurred: {e}")
            return None # Fatal error, do not retry

    if report_content is None:
        print(f"   - ❌ [Analyst] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return None

    output_dir = os.path.dirname(quantitative_output_path)
    base_filename = os.path.splitext(os.path.basename(quantitative_output_path))[0].replace('_quantitative_output', '')
    
    report_filename = f"{base_filename}_Market_Profile.txt"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    return report_path

def _get_market_profiler_prompt() -> str:
    """Contains the master instructions for the objective AI Analyst (OHLC-only)."""
    return """
You are 'QuantLens', a senior quantitative data analyst. Your sole purpose is to interpret statistical market data and present it as a clear, factual, and unbiased 'Market Profile'.

ABSOLUTE CONSTRAINTS (READ CAREFULLY):
- Data available: ONLY OHLC time-series data and derived statistics from OHLC.
- Forbidden: Any use or mention of indicators (RSI, MACD, MAs, Bollinger, etc.), volume, order flow, bid/ask, tick data, or anything not derivable purely from OHLC.
- Your language must reflect pure price-action reasoning (candles, wicks, highs/lows, structure, gaps, sessions).

CRITICAL INSTRUCTIONS:
1. Be Objective: Your report must be purely descriptive. State the statistical facts and their direct implications.
2. DO NOT SUGGEST STRATEGIES: Under no circumstances should you mention trading strategies, entries, exits, or any form of strategic advice. Your job is to present the "what," not the "how."
3. Focus on Scalping Edges: In your interpretation, highlight anomalies relevant for short-term scalping.
   - Which key levels show higher probability of immediate rejection or liquidity sweeps?
   - What is the nature of intra-candle movement? Efficient vs. reversal-prone?
   - Which sessions show larger/smaller ranges or more consistent behaviors?

Report Structure:
- Section 1: Market Character Summary (OHLC-only)
- Section 2: Intra-Candle Path Analysis (Efficient vs. Reversal)
- Section 3: Key Level Reaction Probabilities (Sweep, Breach-and-Continue, Consolidation Rejection)
- Section 4: Session Behavior Highlights (ranges, gaps, opens/closes)
"""
