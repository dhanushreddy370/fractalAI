"""
The "Brain" - New Agent: AI Market Structure Analyzer

This agent specializes in identifying and analyzing market structure patterns
from pure OHLC data. It detects higher highs, lower lows, structure breaks,
trend changes, and multi-timeframe structure alignment.

v1.0 - Initial implementation focusing on pure OHLC market structure analysis.
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
    """Executes market structure analysis from quantitative data."""
    print("   - [Market Structure] Loading quantitative data for structure analysis...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: 
        config = json.load(f)
    with open(quantitative_output_path, 'r') as f: 
        quantitative_data = json.load(f)

    system_prompt = _get_market_structure_prompt()
    user_prompt = f"""
Analyze the market structure patterns from this OHLC-based quantitative data.
Focus on identifying structural patterns, trend changes, and price behavior at key levels.

QUANTITATIVE DATA:
{json.dumps(quantitative_data, indent=2)}
"""

    print(f"   - [Market Structure] Sending data to {config['model_name']} for structure analysis...")
    
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
            print(f"   - ⚠️ [Market Structure] API timeout. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Market Structure] API error: {e}")
            return None

    if analysis_content is None:
        print(f"   - ❌ [Market Structure] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return None

    output_dir = os.path.dirname(quantitative_output_path)
    base_filename = os.path.splitext(os.path.basename(quantitative_output_path))[0].replace('_quantitative_output', '')
    
    report_filename = f"{base_filename}_Market_Structure_Analysis.txt"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(analysis_content)
    return report_path

def _get_market_structure_prompt() -> str:
    """Instructions for the Market Structure Analyzer."""
    return """
You are 'StructureMap', an expert market structure analyst specializing in pure OHLC price action analysis.

ABSOLUTE CONSTRAINTS:
- Use ONLY OHLC data and patterns derivable from Open, High, Low, Close values.
- NO technical indicators, volume analysis, or order flow concepts.
- Focus on pure price structure: highs, lows, candlestick formations, support/resistance levels.

Your Mission:
Analyze the provided quantitative data and produce a comprehensive Market Structure Analysis report.

Focus Areas:
1. Higher High/Lower Low Patterns: Identify trend structure from swing points
2. Market Structure Breaks: Detect when structure shifts from bullish to bearish or vice versa
3. Support/Resistance Zones: Key levels where price has historically reacted
4. Multi-Timeframe Structure: How different timeframes align or conflict
5. Structural Efficiency: How cleanly price moves between levels
6. Session-Based Structure: How structure evolves during different trading sessions

Report Structure:
- Section 1: Overall Market Structure Classification (Trending Up/Down/Ranging)
- Section 2: Key Structural Levels (Support/Resistance with historical significance)
- Section 3: Structure Break Analysis (Recent shifts in market character)
- Section 4: Multi-Timeframe Structure Assessment (HTF vs LTF alignment)
- Section 5: Structural Trading Implications (What the structure suggests for price action)

Write in a clear, analytical style focusing on factual structural observations from the OHLC data.
"""
