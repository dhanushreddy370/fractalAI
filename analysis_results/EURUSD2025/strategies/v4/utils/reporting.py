import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_report(account, price_data_df, output_dir, base_filename="strategy_report"):
    """
    Generates a comprehensive performance report for the EUR/USD Momentum Scalper
    """
    print(f"\n--- Generating Performance Report ---")

    if not account.trade_log:
        print("No trades were executed. Cannot generate a report.")
        return

    df = pd.DataFrame(account.trade_log)

    # Setup output directories
    analysis_output_dir = os.path.join(output_dir, f"{base_filename}_analysis")
    os.makedirs(analysis_output_dir, exist_ok=True)
    
    report_path = os.path.join(analysis_output_dir, f"{base_filename}_full_report.txt")
    equity_chart_path = os.path.join(analysis_output_dir, f"{base_filename}_equity_curve.png")
    trade_log_path = os.path.join(output_dir, f"{base_filename}_trade_log.csv")

    # Data preparation
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df['win'] = df['net_pnl'] > 0
    df['day_of_week'] = df['entry_time'].dt.day_name()
    df['holding_period_mins'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 60
    df['sl_pips'] = abs(df['entry_price'] - df['sl_price']) / 0.0001
    df = df.sort_values('exit_time').reset_index(drop=True)

    # Equity curve calculation
    initial_capital = account.initial_balance
    df['equity'] = initial_capital + df['net_pnl'].cumsum()
    daily_equity = df.groupby(df['exit_time'].dt.date)['equity'].last()
    start_date = daily_equity.index.min() - pd.Timedelta(days=1) if not daily_equity.empty else pd.to_datetime('today') - pd.Timedelta(days=1)
    daily_equity = pd.concat([pd.Series([initial_capital], index=[start_date]), daily_equity])
    daily_returns = daily_equity.pct_change().dropna()

    # Key metrics calculation
    final_capital = df['equity'].iloc[-1]
    total_net_pnl = final_capital - initial_capital
    total_net_pnl_pct = (total_net_pnl / initial_capital) * 100
    win_rate = df['win'].mean() * 100
    total_trades = len(df)
    
    profit_factor = abs(df[df['net_pnl'] > 0]['net_pnl'].sum() / 
                       df[df['net_pnl'] < 0]['net_pnl'].sum()) if df[df['net_pnl'] < 0]['net_pnl'].sum() != 0 else np.inf
    
    avg_win = df[df['win']]['net_pnl'].mean() if df['win'].any() else 0
    avg_loss = abs(df[~df['win']]['net_pnl'].mean()) if not df['win'].all() else 0
    expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
    
    df['running_max'] = df['equity'].cummax()
    df['drawdown'] = df['running_max'] - df['equity']
    max_drawdown = df['drawdown'].max()
    max_drawdown_pct = (max_drawdown / df['running_max'].max()) * 100 if df['running_max'].max() > 0 else 0
    
    # Level performance analysis
    level_performance = {}
    if 'level_type' in df.columns:
        for level_type in df['level_type'].unique():
            level_trades = df[df['level_type'] == level_type]
            if len(level_trades) > 0:
                level_win_rate = level_trades['win'].mean() * 100
                level_pf = abs(level_trades[level_trades['net_pnl'] > 0]['net_pnl'].sum() / 
                              level_trades[level_trades['net_pnl'] < 0]['net_pnl'].sum()) if level_trades[level_trades['net_pnl'] < 0]['net_pnl'].sum() != 0 else np.inf
                level_performance[level_type] = {
                    'win_rate': level_win_rate,
                    'profit_factor': level_pf,
                    'trades': len(level_trades)
                }

    # Generate text report
    with open(report_path, 'w') as f:
        f.write("="*50 + "\n" + "=    EUR/USD Momentum Scalper Performance Report    =\n" + "="*50 + "\n\n")
        f.write("--- I. Overall Performance Summary ---\n")
        f.write(f"Initial Capital:           ${initial_capital:,.2f}\n")
        f.write(f"Final Capital:             ${final_capital:,.2f}\n")
        f.write(f"Total Net Profit:          ${total_net_pnl:,.2f} ({total_net_pnl_pct:.2f}%)\n")
        f.write(f"Maximum Drawdown:          ${max_drawdown:,.2f} ({max_drawdown_pct:.2f}%)\n\n")
        
        f.write("--- II. Trading Metrics ---\n")
        f.write(f"Total Trades:              {total_trades}\n")
        f.write(f"Win Rate:                  {win_rate:.2f}%\n")
        f.write(f"Profit Factor:             {profit_factor:.2f}\n")
        f.write(f"Expectancy per Trade:      ${expectancy:,.2f}\n")
        f.write(f"Average Win:               ${avg_win:,.2f}\n")
        f.write(f"Average Loss:              ${avg_loss:,.2f}\n\n")
        
        f.write("--- III. Key Level Performance ---\n")
        for level, stats in level_performance.items():
            f.write(f"{level}: {stats['trades']} trades, {stats['win_rate']:.1f}% win rate, PF: {stats['profit_factor']:.2f}\n")
        f.write("\n")
        
        f.write("--- IV. Trade Duration Analysis ---\n")
        f.write(f"Average Holding Period:    {df['holding_period_mins'].mean():.1f} minutes\n")
        f.write(f"Median Holding Period:     {df['holding_period_mins'].median():.1f} minutes\n")
        f.write(f"Shortest Trade:           {df['holding_period_mins'].min():.1f} minutes\n")
        f.write(f"Longest Trade:            {df['holding_period_mins'].max():.1f} minutes\n\n")

    print(f"Comprehensive text report saved to '{report_path}'")

    # Generate equity curve chart
    try:
        plt.figure(figsize=(12, 6))
        plt.plot(df['exit_time'], df['equity'], label='Equity Curve', linewidth=2)
        plt.fill_between(df['exit_time'], df['running_max'], df['equity'], 
                        alpha=0.3, label='Drawdown')
        plt.title('Equity Curve', fontsize=16)
        plt.xlabel('Time')
        plt.ylabel('Account Balance ($)')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(equity_chart_path)
        plt.close()
        print(f"Equity curve chart saved to '{equity_chart_path}'")
    except Exception as e:
        print(f"Error generating equity chart: {e}")

    # Save trade log
    try:
        df.to_csv(trade_log_path, index=False)
        print(f"Trade log saved to '{trade_log_path}'")
    except Exception as e:
        print(f"Error saving trade log: {e}")

    print("\n--- Analysis Complete ---")