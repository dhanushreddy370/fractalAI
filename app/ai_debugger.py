"""
The "Brain" - Stage 6a: The Specialist Debugger.

This is a new, highly specialized agent introduced to streamline the optimization
loop. Its sole purpose is to diagnose and propose fixes for crashed backtesters.
Version: 1.0
"""
import json
import os
import re
import time
from openai import OpenAI, APITimeoutError

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

def run(backtest_error_log: str) -> dict:
    """
    Executes the AI crash analysis process.

    Args:
        backtest_error_log: A string containing the stderr output from the crashed backtester.
    """
    print("   - [Debugger] Loading config and crash log...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')

    try:
        with open(config_path, 'r') as f: config = json.load(f)
    except Exception as e:
        print(f"   - ❌ [Debugger] ERROR: Failed to load config file. {e}")
        return None

    # If the log is empty, provide a specific message for the AI
    if not backtest_error_log.strip():
        backtest_error_log = "The backtester crashed silently with no error output to stderr. This could be due to an early sys.exit() call, an invalid command-line argument implementation, or a broken import statement."

    system_prompt = _get_debugger_prompt()
    user_prompt = f"""
The backtester for this strategy version failed to execute. Your task is to act as an expert Python debugger. 
Analyze the provided error log, determine the root cause, and suggest a single, specific code change to fix the bug for the next version.

--- BACKTESTER CRASH LOG ---
{backtest_error_log}
----------------------------
"""

    print(f"   - [Debugger] Sending crash log to {config['model_name']} for analysis...")
    
    raw_ai_response = None
    for attempt in range(MAX_RETRIES):
        try:
            client = OpenAI(base_url=config['api_base_url'], api_key=config['api_key'])
            response = client.chat.completions.create(
                model=config['model_name'],
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                response_format={"type": "json_object"},
                temperature=0.05,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            raw_ai_response = response.choices[0].message.content
            break 
        except APITimeoutError:
            delay = RETRY_DELAY_SECONDS * (2**attempt)
            print(f"   - ⚠️ [Debugger] API call timed out. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Debugger] An unexpected API error occurred: {e}")
            return None

    if raw_ai_response is None:
        print(f"   - ❌ [Debugger] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return None

    print("   - [Debugger] AI has completed the analysis.")
    debug_results = _clean_and_parse_json(raw_ai_response)

    if not debug_results:
        print("   - ❌ [Debugger] CRITICAL ERROR: AI returned invalid JSON. Cannot proceed.")
        print("   - Raw AI Response:", raw_ai_response)
        return None

    return debug_results

def _get_debugger_prompt() -> str:
    """Contains the master instructions for the AI Debugger."""
    return """
You are 'CodeMedic', an expert Python developer and quantitative analyst specializing in debugging complex trading algorithms. Your sole mission is to find and fix bugs in code with surgical precision.

**Your Task:**
You will be given the full error traceback from a Python script that failed to execute. Your mission is to perform a root cause analysis and propose a single, specific code fix.

**Your Analytical Process:**
1.  **Analyze the Traceback:** Read the error log from the bottom up. Identify the exact line of code that caused the crash and the type of error (e.g., `KeyError`, `ValueError`, `ImportError`).
2.  **Formulate a Hypothesis:** Based on the error and code context, determine the most likely reason for the bug. For example, a `ValueError: file not found` suggests the script was passed an incorrect path. A `KeyError` on a DataFrame suggests the AI Coder may have used an incorrect column name.
3.  **Propose a Specific Fix:** Generate a single, actionable instruction for the AI Coder. This instruction must be a clear and concise coding change. It should be a direct command. For example: "In `backtester.py`, modify the `argparse` setup to accept the data file as an absolute path to fix the `ValueError`." or "In `pattern_engine.py`, correct the DataFrame column access from `df['time_stamp']` to `df['time']` to fix the `KeyError`."

**Output Format:**
Your response MUST be a single JSON object with two keys:
1.  `forensic_analysis`: A detailed, multi-paragraph text summary explaining the root cause of the bug.
2.  `suggested_changes`: A JSON array containing a single string. This string is the specific instruction on how to fix the code in the next version.
"""
