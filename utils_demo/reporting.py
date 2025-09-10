import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from tqdm import tqdm

"""
Phase 5: The Verdict - Comprehensive Performance & Forensics Analysis

This is the ultimate, all-in-one analysis module. It is designed to read the
trade log from a simulator and generate a full suite of quantitative,
backtesting, and forensic metrics, including detailed stop-loss analysis.

UPDATE:
- Added a new section for Time-Based Metrics (Waiting Period, Setup Period).
"""

def generate_report(account, price_data_df, output_dir, base_filename="strategy_report"):
    """
    Generates a comprehensive performance report, including advanced metrics,
    forensic analysis of losing trades, and stop-loss distribution.
    """
    print(f"\n--- Generating Comprehensive Performance & Forensics Report ---")

    if not account.trade_log:
        print("No trades were executed. Cannot generate a report.")
        return

    df = pd.DataFrame(account.trade_log)

    # --- Setup Output Directories and Paths ---
    analysis_output_dir = os.path.join(output_dir, f"{base_filename}_analysis")
    if not os.path.exists(analysis_output_dir): os.makedirs(analysis_output_dir)
    report_path = os.path.join(analysis_output_dir, f"{base_filename}_full_report.txt")
    equity_chart_path = os.path.join(analysis_output_dir, f"{base_filename}_equity_curve.png")
    forensics_chart_path = os.path.join(analysis_output_dir, f"{base_filename}_forensics_pie.png")
    sl_dist_chart_path = os.path.join(analysis_output_dir, f"{base_filename}_sl_distribution.png")
    trade_log_path = os.path.join(output_dir, f"{base_filename}_trade_log.csv")

    # --- 1. Data Preparation & Enrichment ---
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    # --- NEW: Handle extra time context from A+ backtester ---
    if 'time_context' in df.columns:
        time_df = df['time_context'].apply(pd.Series)
        df['interaction_time'] = pd.to_datetime(time_df['interaction_time'])
        df['sl_hit_time'] = pd.to_datetime(time_df['sl_hit_time'])
        df['waiting_period_mins'] = (df['entry_time'] - df['interaction_time']).dt.total_seconds() / 60
        df['setup_period_mins'] = (df['entry_time'] - df['sl_hit_time']).dt.total_seconds() / 60
    
    df['win'] = df['net_pnl'] > 0
    df['day_of_week'] = df['entry_time'].dt.day_name()
    df['holding_period_mins'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 60
    df['sl_pips'] = abs(df['entry_price'] - df['sl_price']) / 0.0001
    df = df.sort_values('exit_time').reset_index(drop=True)

    # --- 2. Equity Curve & Daily Returns for Advanced Metrics ---
    initial_capital = account.initial_balance
    df['equity'] = initial_capital + df['net_pnl'].cumsum()
    daily_equity = df.groupby(df['exit_time'].dt.date)['equity'].last()
    start_date = daily_equity.index.min() - pd.Timedelta(days=1) if not daily_equity.empty else pd.to_datetime('today') - pd.Timedelta(days=1)
    daily_equity = pd.concat([pd.Series([initial_capital], index=[start_date]), daily_equity])
    daily_returns = daily_equity.pct_change().dropna()
    daily_returns = daily_returns[daily_returns != 0]

    # --- 3. Comprehensive Metric Calculations ---
    final_capital = df['equity'].iloc[-1]
    total_net_pnl = final_capital - initial_capital
    total_net_pnl_pct = (total_net_pnl / initial_capital) * 100
    win_rate = df['win'].mean() * 100
    total_trades = len(df)
    profit_factor = df[df['net_pnl'] > 0]['net_pnl'].sum() / abs(df[df['net_pnl'] < 0]['net_pnl'].sum()) if abs(df[df['net_pnl'] < 0]['net_pnl'].sum()) > 0 else np.inf
    avg_win = df[df['win']]['net_pnl'].mean() if df['win'].any() else 0
    avg_loss = abs(df[~df['win']]['net_pnl'].mean()) if not df['win'].all() else 0
    expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
    df['running_max'] = df['equity'].cummax()
    df['drawdown'] = df['running_max'] - df['equity']
    max_drawdown = df['drawdown'].max()
    max_drawdown_pct = (max_drawdown / df['running_max'].max()) * 100 if df['running_max'].max() > 0 else 0
    total_duration_years = (df['exit_time'].iloc[-1] - df['entry_time'].iloc[0]).days / 365.25 if total_trades > 1 else 0
    cagr = ((final_capital / initial_capital) ** (1 / total_duration_years) - 1) * 100 if total_duration_years > 0 else 0
    sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
    downside_returns = daily_returns[daily_returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252) if not downside_returns.empty else 0
    sortino_ratio = (daily_returns.mean() * 252) / downside_std if downside_std > 0 else np.inf
    calmar_ratio = cagr / max_drawdown_pct if max_drawdown_pct > 0 else np.inf
    df['streak_counter'] = df['win'].ne(df['win'].shift()).cumsum()
    streaks = df.groupby('streak_counter')['win'].count()
    win_streaks, loss_streaks = streaks[df.groupby('streak_counter')['win'].first()], streaks[~df.groupby('streak_counter')['win'].first()]
    max_win_streak, max_loss_streak = (win_streaks.max() if not win_streaks.empty else 0), (loss_streaks.max() if not loss_streaks.empty else 0)

    # --- 4. Stop-Loss Analysis ---
    max_sl, min_sl, avg_sl = df['sl_pips'].max(), df['sl_pips'].min(), df['sl_pips'].mean()
    sl_bins = [0, 5, 10, 15, 20, np.inf]
    sl_labels = ['0-5 pips', '5-10 pips', '10-15 pips', '15-20 pips', '20+ pips']
    df['sl_range'] = pd.cut(df['sl_pips'], bins=sl_bins, labels=sl_labels, right=False)
    sl_distribution = df['sl_range'].value_counts().sort_index()

    # --- 5. Trade Timing Forensics (Analysis of Losing Trades) ---
    timing_results = []
    losing_trades = df[~df['win']]
    if price_data_df is not None and not price_data_df.empty:
        price_data_df.index = pd.to_datetime(price_data_df.index)
        for _, trade in tqdm(losing_trades.iterrows(), total=len(losing_trades), desc="Analyzing Losing Trades"):
            entry_time = trade['entry_time']
            future_candles = price_data_df.loc[entry_time:].head(101).iloc[1:]
            if len(future_candles) < 100: continue
            tp_hit = (future_candles['high'].max() >= trade['tp_price']) if trade['trade_type'] == 'BUY' else (future_candles['low'].min() <= trade['tp_price'])
            timing_results.append("Entry Too Early" if tp_hit else "Directional Bias Wrong")
    timing_analysis_counts = pd.Series(timing_results).value_counts()

    # --- 6. Generate Final Report File ---
    with open(report_path, 'w') as f:
        f.write("="*50 + "\n" + "=    A+ Strategy Performance & Forensics Report    =\n" + "="*50 + "\n\n")
        f.write("--- I. Overall Performance Summary ---\n")
        f.write(f"Initial Capital:           ${initial_capital:,.2f}\n")
        f.write(f"Final Capital:             ${final_capital:,.2f}\n")
        f.write(f"Total Net Profit:          ${total_net_pnl:,.2f} ({total_net_pnl_pct:.2f}%)\n")
        f.write(f"CAGR:                      {cagr:.2f}%\n")
        f.write(f"Maximum Drawdown:          ${max_drawdown:,.2f} ({max_drawdown_pct:.2f}%)\n\n")
        f.write("--- II. Backtesting Metrics ---\n")
        f.write(f"Total Trades:              {total_trades}\n")
        f.write(f"Win Rate:                  {win_rate:.2f}%\n")
        f.write(f"Profit Factor:             {profit_factor:.2f}\n")
        f.write(f"Expectancy per Trade:      ${expectancy:,.2f}\n")
        f.write(f"Average Win:               ${avg_win:,.2f}\n")
        f.write(f"Average Loss:              ${avg_loss:,.2f}\n")
        f.write(f"Longest Winning Streak:    {int(max_win_streak)} trades\n")
        f.write(f"Longest Losing Streak:     {int(max_loss_streak)} trades\n\n")
        f.write("--- III. Advanced Performance Ratios ---\n")
        f.write(f"Sharpe Ratio:              {sharpe_ratio:.2f}\n")
        f.write(f"Sortino Ratio:             {sortino_ratio:.2f}\n")
        f.write(f"Calmar Ratio:              {calmar_ratio:.2f}\n\n")
        f.write("--- IV. Stop-Loss Analysis ---\n")
        f.write(f"Minimum SL:                {min_sl:.2f} pips\n")
        f.write(f"Maximum SL:                {max_sl:.2f} pips\n")
        f.write(f"Average SL:                {avg_sl:.2f} pips\n\n")
        f.write("SL Distribution:\n" + sl_distribution.to_string() + "\n\n")
        
        # --- NEW: Time Analysis Section ---
        if 'waiting_period_mins' in df.columns:
            f.write("--- V. Time Analysis ---\n")
            f.write("Waiting Period (Interaction to Entry):\n")
            f.write(f"  - Average: {df['waiting_period_mins'].mean():.2f} mins\n")
            f.write(f"  - Median:  {df['waiting_period_mins'].median():.2f} mins\n\n")
            f.write("Setup Period (SL Hit to Entry):\n")
            f.write(f"  - Average: {df['setup_period_mins'].mean():.2f} mins\n")
            f.write(f"  - Median:  {df['setup_period_mins'].median():.2f} mins\n\n")
            f.write("Holding Period (Entry to Exit):\n")
            f.write(f"  - Average: {df['holding_period_mins'].mean():.2f} mins\n")
            f.write(f"  - Median:  {df['holding_period_mins'].median():.2f} mins\n\n")

        f.write("--- VI. Trade Timing Forensics (Analysis of Losing Trades) ---\n")
        if not timing_analysis_counts.empty:
            f.write(timing_analysis_counts.to_string() + "\n\n--- Percentages ---\n")
            f.write((timing_analysis_counts / timing_analysis_counts.sum() * 100).round(2).to_string())
        else: f.write("No losing trades to analyze.")
        f.write("\n" + "="*50 + "\n")

    print(f"Comprehensive text report saved to '{report_path}'")

    # --- 7. Generate and Save Charts ---
    # (Chart generation code remains the same)
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.plot(df['exit_time'], df['equity'], label='Equity Curve', color='dodgerblue', linewidth=2)
        ax.fill_between(df['exit_time'], df['running_max'], df['equity'], facecolor='red', alpha=0.3, label='Drawdown')
        ax.set_title(f'{base_filename} Equity Curve', fontsize=16)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Account Balance ($)', fontsize=12)
        ax.legend()
        ax.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(equity_chart_path)
        plt.close()
        print(f"Equity curve chart saved to '{equity_chart_path}'")
    except Exception as e: print(f"[ERROR] Could not generate equity curve chart: {e}")

    try:
        plt.figure(figsize=(12, 7))
        sl_distribution.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title('Stop-Loss Distribution', fontsize=16)
        plt.xlabel('SL Size (Pips)', fontsize=12)
        plt.ylabel('Number of Trades', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.savefig(sl_dist_chart_path)
        plt.close()
        print(f"Stop-loss distribution chart saved to '{sl_dist_chart_path}'")
    except Exception as e: print(f"[ERROR] Could not generate SL distribution chart: {e}")

    if not timing_analysis_counts.empty:
        try:
            plt.figure(figsize=(10, 8))
            plt.pie(timing_analysis_counts, labels=timing_analysis_counts.index, autopct='%1.1f%%', startangle=140, colors=['#ff6666', '#66b3ff'])
            plt.title(f'Forensic Analysis of Losing Trades', fontsize=16)
            plt.savefig(forensics_chart_path)
            plt.close()
            print(f"Losing trades forensics chart saved to '{forensics_chart_path}'")
        except Exception as e: print(f"[ERROR] Could not generate forensics pie chart: {e}")

    # --- 8. Save Final Trade Log ---
    try:
        df.to_csv(trade_log_path, index=False)
        print(f"Final trade log saved to '{trade_log_path}'")
    except Exception as e: print(f"[ERROR] Could not save final trade log: {e}")

    print("\n--- Analysis Complete ---")
