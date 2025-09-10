"""
The "Brain" - Stage 6b: The Performance Analyst & Optimizer.

This agent analyzes backtest results to find weaknesses and suggest data-driven
improvements. It can now also handle "zero-trade" scenarios.
Version: 2.5 - Corrected openai import error.
"""
import json
import os
import pandas as pd
from openai import OpenAI, APITimeoutError
import re
import time

# --- Constants for API call resilience ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 180.0

def _clean_and_parse_json(raw_response: str) -> dict:
    """Cleans the raw string response from the LLM to extract a valid JSON object."""
    match = re.search(r'```(json)?\s*({.*})\s*```', raw_response, re.DOTALL)
    if match:
        json_str = match.group(2)
    else:
        start = raw_response.find('{')
        end = raw_response.rfind('}')
        if start != -1 and end != -1:
            json_str = raw_response[start:end+1]
        else:
            return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def run(results_dir: str, zero_trades: bool = False) -> dict:
    """
    Executes the AI optimization and forensic analysis process.

    Args:
        results_dir: Path to the backtest results directory.
        zero_trades: A boolean flag indicating if the backtest ran but took no trades.
    """
    print("   - [Optimizer] Loading config and backtest results...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')

    performance_report = ""
    losing_trades_summary = ""
    
    try:
        with open(config_path, 'r') as f: config = json.load(f)
        
        if zero_trades:
            print("   - [Optimizer] ⚠️ Activating Zero-Trade analysis protocol.")
            system_prompt = _get_zero_trade_analyst_prompt()
            user_prompt = "The backtest for this strategy version completed successfully but resulted in zero trades. Your task is to analyze why this might have happened and suggest specific, actionable changes to the strategy rules to increase its trading frequency. Focus on broadening the entry conditions."
        else:
            report_file = next((f for f in os.listdir(results_dir) if f.endswith('_report.txt')), None)
            trade_log_file = next((f for f in os.listdir(results_dir) if f.endswith('_trade_log.csv')), None)

            if not report_file or not trade_log_file:
                 raise FileNotFoundError("Could not find report.txt or trade_log.csv in the results directory.")

            print("   - [Optimizer] Found performance report and trade log.")
            with open(os.path.join(results_dir, report_file), 'r', encoding='utf-8') as f:
                performance_report = f.read()
            
            trade_log_df = pd.read_csv(os.path.join(results_dir, trade_log_file))
            losing_trades_summary = trade_log_df[trade_log_df['net_pnl'] <= 0].head(10).to_string()

            system_prompt = _get_optimizer_prompt()
            user_prompt = f"""
Here is the performance report and a summary of the first 10 losing trades.
Your task is to conduct a deep forensic analysis and return your findings as a single JSON object.

--- PERFORMANCE REPORT ---
{performance_report}
--------------------------

--- LOSING TRADES SUMMARY ---
{losing_trades_summary}
---------------------------
"""

    except Exception as e:
        print(f"   - ❌ [Optimizer] ERROR: Failed to load results. {e}")
        return None

    print(f"   - [Optimizer] Sending data to {config['model_name']} for analysis...")
    
    raw_ai_response = None
    for attempt in range(MAX_RETRIES):
        try:
            client = OpenAI(base_url=config['api_base_url'], api_key=config['api_key'])
            response = client.chat.completions.create(
                model=config['model_name'],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            raw_ai_response = response.choices[0].message.content
            break 
        except APITimeoutError:
            delay = RETRY_DELAY_SECONDS * (2**attempt)
            print(f"   - ⚠️ [Optimizer] API call timed out. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Optimizer] An unexpected API error occurred: {e}")
            return None

    if raw_ai_response is None:
        print(f"   - ❌ [Optimizer] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return {"decision": "OPTIMIZATION_COMPLETE", "forensic_analysis": "API call failed.", "suggested_changes": []}

    print("   - [Optimizer] AI has completed the analysis.")
    optimization_results = _clean_and_parse_json(raw_ai_response)

    if not optimization_results:
        print("   - ❌ [Optimizer] CRITICAL ERROR: AI returned invalid JSON. Cannot proceed.")
        print("   - Raw AI Response:", raw_ai_response)
        return {"decision": "OPTIMIZATION_COMPLETE", "forensic_analysis": "Invalid JSON from AI.", "suggested_changes": []}

    # If the AI was in zero-trade mode, force the decision to continue.
    if zero_trades:
        optimization_results['decision'] = "CONTINUE_OPTIMIZATION"

    return optimization_results

def _get_optimizer_prompt() -> str:
    """Contains the master instructions for the AI Performance Analyst."""
    return """
You are 'OptimusQuant', a senior performance analyst at a world-class high-frequency trading firm. Your only job is to find weaknesses in trading strategies and propose concrete, data-driven improvements to enhance their profitability and robustness. You are brutally honest and focus purely on quantitative metrics.

**Your Task:**
You will be given the backtesting performance report and the full trade log for a strategy. Your mission is to conduct a deep forensic analysis and decide if the strategy can be improved.

**Your Analytical Process:**
1.  **Analyze Performance Metrics:** Scrutinize the report. Is the Sharpe Ratio below 1.0? Is the Profit Factor below 1.5? Is the maximum drawdown too high compared to the total return?
2.  **Forensic Log Analysis:** Scrutinize the trade log. Look for patterns in losing trades. Do they all occur at a specific time? Do they share a common setup? Are they all stopped out by the same amount? Is the holding time for losers much longer than for winners?
3.  **Propose Specific Changes:** Based on your analysis, generate a list of precise, actionable changes to the strategy rules. Do not be vague. Instead of "improve stop loss," suggest "Change the stop loss from a fixed 1.5 pips to a dynamic stop placed 0.5 pips above the high of the entry setup candle."
4.  **Make a Decision:** Based on the potential for improvement, make a final decision. If key metrics are weak or you've identified clear failure patterns, continue optimizing. If the metrics are strong (e.g., Sharpe > 1.5, Profit Factor > 1.8) and there are no more obvious patterns to exploit, conclude the optimization.

**Output Format:**
Your response MUST be a single JSON object with three keys:
1.  `forensic_analysis`: A detailed, multi-paragraph text summary of your findings and the reasoning behind your proposed changes.
2.  `suggested_changes`: A JSON array of strings, where each string is a specific instruction for the AI Strategist to implement in the next version. If no changes are needed, provide an empty array.
3.  `decision`: A single string, either `"CONTINUE_OPTIMIZATION"` or `"OPTIMIZATION_COMPLETE"`.
"""

def _get_zero_trade_analyst_prompt() -> str:
    """A new set of instructions for when the Optimizer needs to analyze a strategy that produced no trades."""
    return """
You are 'OptimusQuant', a senior performance analyst. You have been tasked with fixing a trading strategy that is too passive and is not executing any trades.

**Your Task:**
The backtest for the current strategy version completed successfully but resulted in **zero trades**. This indicates the entry conditions are too strict or narrow. Your mission is to propose specific, data-driven changes to broaden the entry criteria and increase the strategy's activity.

**Your Analytical Process:**
1.  **Hypothesize the Cause:** The strategy rules are too restrictive. Common causes include:
    - An indicator threshold that is rarely met (e.g., RSI must be < 5).
    - A price-based condition that is too precise (e.g., price must touch a level to the exact pip).
    - A combination of multiple filters that are unlikely to align simultaneously.
2.  **Propose Specific Changes:** Generate a list of precise, actionable changes to the strategy rules to make them less restrictive. Do not be vague. Your goal is to get the strategy to take *some* trades so you can analyze its performance. Examples:
    - "Increase the RSI entry threshold from 20 to 30 for long trades."
    - "Widen the price level touch tolerance from 0.5 pips to 1.5 pips."
    - "Remove the secondary moving average filter from the entry conditions."

**Output Format:**
Your response MUST be a single JSON object with three keys:
1.  `forensic_analysis`: A detailed, multi-paragraph text summary hypothesizing why the strategy took no trades.
2.  `suggested_changes`: A JSON array of strings, where each string is a specific instruction for the AI Strategist to implement to broaden the entry criteria.
3.  `decision`: This value is ignored in this mode, but for format consistency, set it to `"CONTINUE_OPTIMIZATION"`.
"""

