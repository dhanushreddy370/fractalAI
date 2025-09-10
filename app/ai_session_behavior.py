"""
The "Brain" - New Agent: AI Session Behavior Specialist

This agent specializes in analyzing session-specific price behavior patterns
from pure OHLC data. It examines how price behaves during different trading
sessions, opening gaps, intraday ranges, and session-to-session relationships.

v1.0 - Initial implementation focusing on pure OHLC session analysis.
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
    """Executes session behavior analysis from quantitative data."""
    print("   - [Session Behavior] Loading quantitative data for session analysis...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: 
        config = json.load(f)
    with open(quantitative_output_path, 'r') as f: 
        quantitative_data = json.load(f)

    system_prompt = _get_session_behavior_prompt()
    user_prompt = f"""
Analyze the session-specific price behavior patterns from this OHLC-based quantitative data.
Focus on identifying how price behaves during different trading sessions and time periods.

QUANTITATIVE DATA:
{json.dumps(quantitative_data, indent=2)}
"""

    print(f"   - [Session Behavior] Sending data to {config['model_name']} for session analysis...")
    
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
            print(f"   - ⚠️ [Session Behavior] API timeout. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Session Behavior] API error: {e}")
            return None

    if analysis_content is None:
        print(f"   - ❌ [Session Behavior] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return None

    output_dir = os.path.dirname(quantitative_output_path)
    base_filename = os.path.splitext(os.path.basename(quantitative_output_path))[0].replace('_quantitative_output', '')
    
    report_filename = f"{base_filename}_Session_Behavior_Analysis.txt"
    report_path = os.path.join(output_dir, report_filename)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(analysis_content)
    return report_path

def _get_session_behavior_prompt() -> str:
    """Instructions for the Session Behavior Specialist."""
    return """
You are 'SessionFlow', an expert session behavior analyst specializing in pure OHLC price action analysis.

ABSOLUTE CONSTRAINTS:
- Use ONLY OHLC data to analyze session-specific price behavior.
- NO technical indicators, volume analysis, or order flow concepts.
- Focus purely on how price opens, moves, and closes during different time periods.

Your Mission:
Analyze the provided quantitative data and produce a comprehensive Session Behavior Analysis report.

Focus Areas:
1. Opening Behavior: How price opens relative to previous session closes (gaps, continuations)
2. Intraday Range Behavior: Range expansion/contraction patterns during sessions
3. Session Close Patterns: How price tends to close relative to session opens and ranges
4. Session-to-Session Relationships: How one session's behavior affects the next
5. Time-of-Day Effects: Specific hourly patterns within sessions
6. Session Efficiency: How efficiently price moves during different sessions

Session Categories to Analyze:
- Asian Session: Typically lower volatility, range-bound behavior
- London Session: Higher volatility, trend establishment
- New York Session: Highest volatility, major moves
- Session Overlaps: London-NY overlap periods

Behavioral Patterns to Identify:
- Gap Patterns: How often and how much gaps occur between sessions
- Range Patterns: Average ranges, range expansion/contraction
- Momentum Patterns: How momentum carries between sessions
- Reversal Patterns: End-of-session reversals or continuations
- Time Decay Patterns: How behavior changes throughout each session

Report Structure:
- Section 1: Session Characterization (Unique traits of each session)
- Section 2: Opening Behavior Analysis (Gap patterns and opening dynamics)
- Section 3: Intraday Range Dynamics (How ranges develop during sessions)
- Section 4: Session Transition Analysis (How sessions hand off to each other)
- Section 5: Optimal Trading Times (Best periods for different types of strategies)

Write in a clear, practical style focusing on actionable insights from session-based OHLC analysis.
"""
