"""
The "Brain" - Stage 4: The Strategy Coder.

This agent generates a complete, runnable backtesting project from a strategy doc.
v2.7 - Enforced exact argparse signature in the prompt to prevent argument mismatch errors.
"""
import json
import os
import re
import time
from openai import OpenAI, APITimeoutError

# --- Constants for API call resilience ---
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5
REQUEST_TIMEOUT_SECONDS = 240.0 # Increased timeout for this complex task

def _clean_and_parse_json(raw_response: str) -> dict:
    """
    Cleans the raw string response from the LLM to extract a valid JSON object.
    """
    # This function remains unchanged.
    match = re.search(r'```(json)?\s*({.*})\s*```', raw_response, re.DOTALL)
    if match:
        json_str = match.group(2)
    else:
        start = raw_response.find('{')
        end = raw_response.rfind('}')
        if start != -1 and end != -1:
            json_str = raw_response[start:end+1]
        else:
            print("   - ❌ [Coder] Sub-Error: Could not find any JSON structure in the AI response.")
            return {"files": []}
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"   - ❌ [Coder] Sub-Error: Failed to parse the extracted JSON string. Error: {e}")
        print(f"   - Extracted String was: {json_str[:500]}...")
        return {"files": []}

def run(strategy_document_path: str, demo_utils: dict, output_dir: str) -> list:
    """
    Executes the AI code generation process.
    """
    print("   - [Coder] Loading config, strategy document, and demo utilities...")
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(os.path.dirname(script_dir), 'config', 'config.json')
    
    with open(config_path, 'r') as f: config = json.load(f)
    with open(strategy_document_path, 'r', encoding='utf-8') as f: strategy_document = f.read()

    system_prompt = _get_coder_prompt()
    
    utils_prompt_string = ""
    for filename, code in demo_utils.items():
        utils_prompt_string += f"\n--- DEMO FILE: {filename} ---\n{code}\n----------------------------------\n"

    user_prompt = f"""
Here is the formal 'Strategy Document' and the 'Demo Utility Files' to use as a template.
Your task is to generate the complete, self-contained Python backtesting project as a single JSON object.

--- STRATEGY DOCUMENT ---
{strategy_document}
-------------------------

--- DEMO UTILITY FILES ---
{utils_prompt_string}
--------------------------
"""

    print(f"   - [Coder] Sending instructions to {config['model_name']} for code generation...")
    
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
            break # Success
        except APITimeoutError:
            delay = RETRY_DELAY_SECONDS * (2**attempt)
            print(f"   - ⚠️ [Coder] API call timed out. Retrying in {delay}s... (Attempt {attempt + 1}/{MAX_RETRIES})")
            time.sleep(delay)
        except Exception as e:
            print(f"   - ❌ [Coder] An unexpected API error occurred: {e}")
            return [] # Fatal error

    if raw_ai_response is None:
        print(f"   - ❌ [Coder] CRITICAL ERROR: API call failed after {MAX_RETRIES} attempts.")
        return []

    # --- ENHANCED DEBUGGING ---
    print("   - [Coder] DEBUG: Raw AI Response received. Cleaning and writing files...")
    # print("vvv--- RAW RESPONSE ---vvv\n", raw_ai_response, "\n^^^--- END RAW RESPONSE ---^^^")
    # --------------------------
    
    parsed_json = _clean_and_parse_json(raw_ai_response)
    files_to_create = parsed_json.get("files", [])

    if not files_to_create:
        print("   - ❌ [Coder] CRITICAL ERROR: AI returned a valid JSON, but the 'files' list was empty or missing.")
        print("   - Raw AI Response:", raw_ai_response)
        return []

    created_files = []
    for file_info in files_to_create:
        filename = file_info.get("filename")
        code = file_info.get("code")
        
        if not filename or not code:
            continue
            
        full_path = os.path.abspath(os.path.join(output_dir, filename))
        
        file_dir = os.path.dirname(full_path)
        os.makedirs(file_dir, exist_ok=True)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(code)
        created_files.append(full_path)
        
    return created_files

def _get_coder_prompt() -> str:
    """Contains the master instructions for the AI Coder (OHLC-only coding)."""
    return """
You are 'CodeGenius', an expert Python developer specializing in quantitative trading systems. Your sole mission is to build complete, robust, and runnable backtesting projects. You are meticulous and always follow the specified output format.

Absolute Constraints:
- Implement strategies using ONLY OHLC price action (no indicators, no order flow, no volume-based logic).
- Do NOT import or compute any technical indicators (e.g., talib, pandas_ta, SMA/EMA/RSI/MACD/Bollinger).

PRIMARY GOAL:
Generate a complete Python backtesting project based on the provided 'Strategy Document' and 'Demo Utility Files'.

OUTPUT FORMAT (ABSOLUTELY MANDATORY):
Your entire response MUST be a single JSON object. The object must have a single key, "files", which is a list of dictionaries. Each dictionary must have two keys: "filename" and "code".

FILE MANIFEST (These are the files you MUST create):
1.  `README.md`: A brief summary of the strategy and how to run the backtester from the command line.
2.  `backtester.py`: The main script that runs the entire backtest.
3.  `utils/__init__.py`: An empty file to make `utils` a Python package.
4.  `utils/data_handler.py`: Customized data loading and preparation logic.
5.  `utils/pattern_engine.py`: Customized logic for OHLC-based patterns (NO indicators).
6.  `utils/account_manager.py`: The trading account simulation.
7.  `utils/reporting.py`: Logic for generating the final report and charts.

SPECIFIC INSTRUCTIONS FOR KEY FILES:
-   For `backtester.py` (CRITICAL):
    -   The very first lines of code MUST be the following path correction block to prevent `ImportError`:
        ```python
        import sys
        import os
        # Add the script's own directory to the Python path to ensure local modules can be found.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.append(script_dir)
        ```
    -   It must handle command-line arguments using Python's `argparse` module. The data file path MUST be a positional argument exactly as:
        `parser.add_argument('data_file', help='Path to the 1-minute data CSV file')`
    -   It must import its dependencies from the `utils` package (e.g., `from utils.data_handler import ...`).
    -   It must save all results into a `results/` subdirectory.

-   For `utils/account_manager.py` (CRITICAL):
    -   You MUST implement realistic market friction:
        -   Variable Spread: add a small random component per trade.
        -   Slippage: entry price slightly worse than requested by a small random amount.

Your purpose is to deliver a flawless, self-contained, and runnable backtesting project that adheres perfectly to these instructions while respecting the OHLC-only constraint.
"""

