"""
The "Brain" - New Agent: AI Support/Resistance Expert

This agent specializes in identifying and analyzing support and resistance levels
from pure OHLC data. It examines level strength, confluence zones, level breaks,
and multi-timeframe level alignment.

v1.0 - Initial implementation focusing on pure OHLC support/resistance analysis.
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
    """Executes support/resistance analysis from quantitative data."""
    print("   - [Support/Resistance] Loading quantitative data for level analysis...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: 
        config = json.load(f)
    with open(quantitative_output_path, 'r') as f: 
        quantitative_data = json.load(f)

    system_prompt = _get_support_resistance_prompt()
    user_prompt = f"""
Analyze the support and resistance level patterns from this OHLC-based quantitative data.
Focus on identifying key levels, their strength, and how price reacts at these levels.

QUANTITATIVE DATA:
{json.dumps(quantitative_data, indent=2)}
"""

    print(f"   - [Support/Resistance] Sending data to {config['model_name']} for level analysis...")
    
    analysis_content = None
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
            analysis_content = response.choices[0].message.content
            break
        except APITimeoutError:
            delay = RETRY_DELAY_SECONDS * (2**attempt)
            print(f"   - ⚠️ [Support/Resistance] API timeout. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Support/Resistance] API error: {e}")
            return None

    if analysis_content is None:
        print(f"   - ❌ [Support/Resistance] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return None

    output_dir = os.path.dirname(quantitative_output_path)
    base_filename = os.path.splitext(os.path.basename(quantitative_output_path))[0].replace('_quantitative_output', '')
    
    report_filename = f"{base_filename}_Support_Resistance_Analysis.txt"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(analysis_content)
    return report_path

def _get_support_resistance_prompt() -> str:
    """Instructions for the Support/Resistance Expert."""
    return """
You are 'LevelMaster', an expert support/resistance analyst specializing in pure OHLC price action analysis.

ABSOLUTE CONSTRAINTS:
- Use ONLY OHLC data to identify and analyze support/resistance levels.
- NO technical indicators, volume analysis, or order flow concepts.
- Focus purely on historical price levels, reactions, and level interactions.

Your Mission:
Analyze the provided quantitative data and produce a comprehensive Support/Resistance Level Analysis report.

Focus Areas:
1. Level Identification: Key historical highs/lows that price has reacted to
2. Level Strength: How many times and how strongly price has reacted at levels
3. Level Types: Horizontal levels, trend lines, session levels, round numbers
4. Level Reactions: Bounce patterns, break patterns, false break patterns
5. Multi-Timeframe Confluence: Where levels from different timeframes align
6. Level Evolution: How levels gain or lose significance over time

Level Categories to Analyze:
- Historical Highs/Lows: Previous significant price extremes
- Session Levels: Asian/London/NY session highs and lows
- Round Numbers: Psychological levels ending in 00, 50, etc.
- Pivot Points: Natural support/resistance from price action
- Trend Lines: Dynamic support/resistance from connecting swing points

Reaction Patterns to Identify:
- Clean Bounces: Price respects level and reverses cleanly
- False Breaks: Price briefly breaks level then reverses
- Liquidity Sweeps: Price breaks level to grab stops then reverses
- Clean Breaks: Price breaks through level and continues
- Retests: Price returns to broken level for confirmation

Report Structure:
- Section 1: Key Level Inventory (Most significant current levels)
- Section 2: Level Strength Analysis (Which levels are most reliable)
- Section 3: Reaction Pattern Statistics (How price typically reacts at levels)
- Section 4: Multi-Timeframe Level Confluence (Where levels align across timeframes)
- Section 5: Level Trading Implications (How to use levels for entries/exits)

Write in a clear, practical style focusing on actionable level analysis from pure OHLC data.
"""
