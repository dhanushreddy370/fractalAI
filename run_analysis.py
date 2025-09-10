"""
FractalAI Analysis Suite - Main Orchestrator

This script is the central nervous system for a multi-agent AI team designed to
autonomously analyze financial market data, generate trading strategies,
write the backtesting code for them, and iteratively optimize them based on
performance.

Version: 6.2 - Robust Results File Checking
"""
import sys
import os
import torch
import json
import subprocess
import glob
import shutil
from app import (quantitative_engine, ai_analyst, ai_strategist, ai_coder, ai_optimizer, ai_debugger,
                 ai_market_structure, ai_candlestick_expert, ai_session_behavior, ai_support_resistance)

MAX_OPTIMIZATION_CYCLES = 5 # Safety limit to prevent infinite loops

def get_data_path_from_user():
    """Interactively prompts for the data file path."""
    while True:
        try:
            path = input("➡️ Please enter the full path to your M1 data CSV file: ")
        except KeyboardInterrupt:
            print("\n\nAnalysis cancelled by user. Exiting.")
            sys.exit()
        if path.lower() in ['quit', 'exit']:
            print("\nAnalysis cancelled by user. Exiting.")
            sys.exit()
        if not os.path.exists(path):
            print(f"\n❌ ERROR: The file was not found at '{path}'. Please check the path and try again.\n")
            continue
        if not os.path.isfile(path):
            print(f"\n❌ ERROR: The path '{path}' points to a directory, not a file. Please provide a path to a valid CSV file.\n")
            continue
        return os.path.abspath(path)

def load_demo_utilities():
    """Loads the content of the demo utility files."""
    utils_dir = 'utils_demo'
    if not os.path.exists(utils_dir): 
        print(f"❌ ERROR: Demo utilities directory '{utils_dir}' not found. Aborting.")
        return None
    demo_utils = {}
    for filename in os.listdir(utils_dir):
        if filename.endswith('.py'):
            with open(os.path.join(utils_dir, filename), 'r', encoding='utf-8') as f:
                demo_utils[filename] = f.read()
    return demo_utils

def find_latest_state(strategy_base_dir, report_dir):
    """Finds the latest completed version and the path to its strategy document."""
    if not os.path.exists(strategy_base_dir):
        return 0, None
        
    version_dirs = glob.glob(os.path.join(strategy_base_dir, 'v[0-9]*'))
    if not version_dirs:
        return 0, None

    latest_version = 0
    for v_dir in version_dirs:
        try:
            version_num = int(os.path.basename(v_dir).replace('v', ''))
            results_path = os.path.join(v_dir, 'results')
            if os.path.exists(results_path) and any(f.endswith('_report.txt') for f in os.listdir(results_path)):
                if version_num > latest_version:
                    latest_version = version_num
        except (ValueError, IndexError):
            continue
    
    if latest_version == 0:
        return 0, None

    base_filename = os.path.basename(os.path.dirname(os.path.dirname(strategy_base_dir)))
    latest_strategy_path = os.path.join(report_dir, f"{base_filename}_Scalping_Strategy_v{latest_version}.txt")
    
    if not os.path.exists(latest_strategy_path):
        return 0, None 

    return latest_version, latest_strategy_path

def save_state(report_dir, history):
    """Saves the optimization history to a JSON file."""
    state_path = os.path.join(report_dir, 'optimization_history.json')
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4)

def load_state(report_dir):
    """Loads the optimization history from a JSON file."""
    state_path = os.path.join(report_dir, 'optimization_history.json')
    if os.path.exists(state_path):
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def _generate_version_control_report(history: list, final_version: int, report_dir: str):
    """Generates a markdown report of the optimization cycles."""
    report_path = os.path.join(report_dir, "Version_Control_Report.md")
    print(f"\n📄 Generating Version Control Report...")
    base_filename = os.path.basename(os.path.dirname(report_dir))
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Strategy Optimization Report: {base_filename}\n\n")
        f.write(f"**Final Optimized Version:** v{final_version}\n\n")
        f.write("---\n\n")

        for i, entry in enumerate(history):
            cycle_type = f"CYCLE {entry['version']}: {entry['type'].upper()}"
            f.write(f"## {cycle_type}\n\n")
            
            f.write(f"**AI's Forensic Analysis:**\n")
            analysis_text = entry['analysis'].replace('\n', '\n> ')
            f.write(f"> {analysis_text}\n\n")
            
            if entry.get('changes'):
                f.write(f"**Suggested Changes for Next Version:**\n")
                for change in entry['changes']:
                    f.write(f"- `{change}`\n")
            else:
                f.write("**Decision:**\n- Optimization Concluded. No further changes suggested.\n")
            f.write("\n---\n\n")
            
    print(f"   - ✅ Report saved to: '{report_path}'")

def main():
    """Main execution function to run the optimization loop."""
    print("🚀 Starting FractalAI Analysis Suite v6.2 (Robust Results Checking)...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"   - Device check: PyTorch detected [{device.upper()}]")

    input_data_path = get_data_path_from_user()
    base_filename = os.path.splitext(os.path.basename(input_data_path))[0]
    
    output_base_dir = os.path.join('analysis_results', base_filename)
    report_dir = os.path.join(output_base_dir, 'reports')
    strategy_base_dir = os.path.join(output_base_dir, 'strategies')
    
    start_version = 1
    run_initial_analysis = True
    previous_strategy_path = None
    optimization_history = []
    
    market_profile_path = os.path.join(report_dir, f"{base_filename}_Market_Profile.txt")

    if os.path.exists(output_base_dir):
        while True:
            choice = input(f"➡️ Previous analysis found for '{base_filename}'.\n   (C)ontinue, or start a (N)ew analysis? [C/N]: ").lower()
            if choice in ['c', 'n']:
                break
            print("   Invalid choice. Please enter 'C' or 'N'.")

        if choice == 'n':
            print("   - 🗑️ Deleting previous analysis to start fresh.")
            shutil.rmtree(output_base_dir)
        else:
            latest_version, prev_strat_path = find_latest_state(strategy_base_dir, report_dir)
            if latest_version > 0 and prev_strat_path:
                print(f"   - ✅ Resuming analysis from last completed version. Starting with v{latest_version + 1}.")
                start_version = latest_version + 1
                previous_strategy_path = prev_strat_path
                optimization_history = load_state(report_dir)
                run_initial_analysis = False
            elif os.path.exists(market_profile_path):
                 print("   - ✅ No completed versions found, but initial analysis exists. Resuming optimization from v1.")
                 start_version = 1
                 optimization_history = []
                 run_initial_analysis = False
            else:
                print("   - ⚠️ Could not find a valid state to resume. Starting a new analysis.")
                shutil.rmtree(output_base_dir)

    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(strategy_base_dir, exist_ok=True)
    
    print(f"\n✅ Input data file found: {os.path.basename(input_data_path)}")
    print(f"   - All outputs will be saved in: '{output_base_dir}'")

    try:
        if run_initial_analysis:
            print("\n--- Initial Analysis Phase ---")
            print("\n[Stage 1] 🔢 Running Quantitative Engine (OHLC-only analysis)...")
            quantitative_output_path = quantitative_engine.run(input_data_path, report_dir)
            
            print("\n[Stage 2a] 🧠 Running AI Analyst (Market Profile)...")
            market_profile_path = ai_analyst.run(quantitative_output_path)
            
            print("\n[Stage 2b] 📊 Running Market Structure Analyzer...")
            structure_analysis_path = ai_market_structure.run(quantitative_output_path)
            
            print("\n[Stage 2c] 🕯️ Running Candlestick Pattern Expert...")
            candlestick_analysis_path = ai_candlestick_expert.run(quantitative_output_path)
            
            print("\n[Stage 2d] ⏰ Running Session Behavior Specialist...")
            session_analysis_path = ai_session_behavior.run(quantitative_output_path)
            
            print("\n[Stage 2e] 📈 Running Support/Resistance Expert...")
            support_resistance_path = ai_support_resistance.run(quantitative_output_path)
            
            print("   - ✅ Enhanced analysis complete. Multiple AI expert reports generated.")
        else:
            print("\n--- Skipping Initial Analysis Phase (Already Complete) ---")

        version = start_version
        final_version = start_version -1
        
        while version <= MAX_OPTIMIZATION_CYCLES:
            print("\n" + "="*50)
            print(f"   OPTIMIZATION CYCLE {version}")
            print("="*50)

            if version == 1:
                print("\n[Stage 3] 💡 Running AI Strategist (Initial Design)...")
                strategy_path = ai_strategist.run(market_profile_path, version)
            else:
                print(f"\n[Stage 3] 💡 Running AI Strategist (Evolving to v{version})...")
                suggested_changes = optimization_history[-1]['changes']
                strategy_path = ai_strategist.run_optimization_cycle(previous_strategy_path, suggested_changes, version)
            
            if not strategy_path:
                print("   - ❌ CRITICAL ERROR: AI Strategist failed. Aborting loop.")
                break
            print(f"   - ✅ Strategist finished. v{version} strategy saved.")
            previous_strategy_path = strategy_path

            print("\n[Stage 4] 💻 Running AI Coder...")
            strategy_version_dir = os.path.join(strategy_base_dir, f'v{version}')
            demo_utils = load_demo_utilities()
            if not demo_utils: sys.exit(1)
            generated_files = ai_coder.run(strategy_path, demo_utils, strategy_version_dir)
            if not generated_files:
                print("   - ❌ CRITICAL ERROR: AI Coder failed. Aborting loop.")
                break
            print(f"   - ✅ Coder finished. v{version} project generated.")
            
            results_dir = os.path.join(strategy_version_dir, 'results')
            os.makedirs(results_dir, exist_ok=True)

            print("\n[Stage 5] 📈 Running Automated Backtest...")
            backtester_path = next((f for f in generated_files if 'backtester' in os.path.basename(f)), None)
            if not backtester_path:
                print("   - ❌ CRITICAL ERROR: No backtester script found. Aborting loop.")
                break
            
            process = subprocess.run(
                [sys.executable, backtester_path, input_data_path],
                cwd=strategy_version_dir, capture_output=True, text=True, check=False
            )
            
            # --- ROBUST DECISION GATE ---
            is_crash = process.returncode != 0
            
            # Check for the actual result files, not just if the directory is empty
            results_exist = (
                any(f.endswith('_report.txt') for f in os.listdir(results_dir)) and
                any(f.endswith('_trade_log.csv') for f in os.listdir(results_dir))
            )

            if is_crash:
                print(f"   - ❌ ERROR: The v{version} backtester CRASHED.")
                print("\n--- Backtester Error Output ---\n", process.stderr, "\n-------------------")
                
                print("\n[Stage 6a] 🩺 Running AI Debugger...")
                results = ai_debugger.run(process.stderr)
                history_entry = { "type": "debug", "version": version }
            elif not results_exist:
                print(f"   - ⚠️ WARNING: The v{version} backtester ran successfully but produced NO RESULT FILES (zero trades).")
                print("\n[Stage 6b] 🧐 Running AI Optimizer (Zero-Trade Protocol)...")
                results = ai_optimizer.run(results_dir, zero_trades=True)
                history_entry = { "type": "optimization (zero trades)", "version": version }
            else: # Successful run with trades
                print(f"   - ✅ Backtester v{version} executed successfully.")
                
                print("\n[Stage 6b] 🧐 Running AI Optimizer...")
                results = ai_optimizer.run(results_dir)
                history_entry = { "type": "optimization", "version": version }

            if not results:
                agent_name = "Debugger" if is_crash else "Optimizer"
                print(f"   - ❌ CRITICAL ERROR: The {agent_name} failed. Aborting loop.")
                break
            
            history_entry['analysis'] = results['forensic_analysis']
            history_entry['changes'] = results.get('suggested_changes', [])
            
            optimization_history.append(history_entry)
            save_state(report_dir, optimization_history)
            final_version = version

            agent_name = "Debugger" if is_crash else "Optimizer"
            print(f"   - ✅ {agent_name} finished.")
            print("   - Forensic Analysis:", results['forensic_analysis'])

            if results.get('decision') == "OPTIMIZATION_COMPLETE":
                print("\n🎉 Optimization Complete! The AI has determined the strategy is robust.")
                print(f"   - The final, best-performing version is v{version}.")
                print(f"   - Project and results are in: '{strategy_version_dir}'")
                break

            version += 1
        else: 
            print(f"\n⚠️  Reached maximum optimization cycles ({MAX_OPTIMIZATION_CYCLES}). Stopping process.")
            print(f"   - The final version is v{version-1} located in the strategies folder.")

        if optimization_history:
            _generate_version_control_report(optimization_history, final_version, report_dir)

    except Exception as e:
        print(f"\n❌ A critical error occurred in the main orchestrator: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

