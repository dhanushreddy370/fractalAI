"""
The "Brain" - New Agent: AI Candlestick Pattern Expert

This agent specializes in identifying and analyzing candlestick patterns
from pure OHLC data. It recognizes single and multi-candle formations,
pattern contexts, and their statistical significance.

v1.0 - Initial implementation focusing on pure OHLC candlestick analysis.
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
    """Executes candlestick pattern analysis from quantitative data."""
    print("   - [Candlestick Expert] Loading quantitative data for pattern analysis...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: 
        config = json.load(f)
    with open(quantitative_output_path, 'r') as f: 
        quantitative_data = json.load(f)

    system_prompt = _get_candlestick_expert_prompt()
    user_prompt = f"""
Analyze the candlestick patterns and formations from this OHLC-based quantitative data.
Focus on pattern recognition, context, and statistical reliability of different formations.

QUANTITATIVE DATA:
{json.dumps(quantitative_data, indent=2)}
"""

    print(f"   - [Candlestick Expert] Sending data to {config['model_name']} for pattern analysis...")
    
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
            print(f"   - ⚠️ [Candlestick Expert] API timeout. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Candlestick Expert] API error: {e}")
            return None

    if analysis_content is None:
        print(f"   - ❌ [Candlestick Expert] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return None

    output_dir = os.path.dirname(quantitative_output_path)
    base_filename = os.path.splitext(os.path.basename(quantitative_output_path))[0].replace('_quantitative_output', '')
    
    report_filename = f"{base_filename}_Candlestick_Pattern_Analysis.txt"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(analysis_content)
    return report_path

def _get_candlestick_expert_prompt() -> str:
    """Instructions for the Candlestick Pattern Expert."""
    return """
You are 'CandleMaster', an expert candlestick pattern analyst specializing in pure OHLC price action analysis.

ABSOLUTE CONSTRAINTS:
- Use ONLY OHLC data to identify candlestick patterns and formations.
- NO technical indicators, volume analysis, or order flow concepts.
- Focus purely on Open, High, Low, Close relationships and candlestick geometry.

Your Mission:
Analyze the provided quantitative data and produce a comprehensive Candlestick Pattern Analysis report.

Focus Areas:
1. Single Candle Patterns: Doji, hammer, shooting star, spinning top, marubozu
2. Multi-Candle Patterns: Engulfing, harami, morning/evening star, three soldiers/crows
3. Pattern Context: How patterns perform at key levels vs. in open space
4. Pattern Reliability: Statistical success rates of different formations
5. Pattern Failures: When and why certain patterns don't work
6. Session-Based Patterns: How patterns behave during different trading sessions

Pattern Categories to Analyze:
- Reversal Patterns: Formations that suggest trend changes
- Continuation Patterns: Formations that suggest trend persistence
- Indecision Patterns: Formations that suggest market uncertainty
- Breakout Patterns: Formations that suggest imminent large moves

Report Structure:
- Section 1: Pattern Frequency Analysis (Most common patterns in the data)
- Section 2: High-Reliability Patterns (Patterns with best success rates)
- Section 3: Context-Dependent Patterns (Patterns that work better in specific conditions)
- Section 4: Pattern Timing Analysis (Best sessions/times for different patterns)
- Section 5: Pattern Trading Implications (How to interpret patterns for scalping)

Write in a clear, educational style focusing on practical pattern recognition from OHLC data.
"""
