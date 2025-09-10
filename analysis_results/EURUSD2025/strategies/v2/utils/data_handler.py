import pandas as pd
import os

def load_and_prepare_data(file_path):
    """
    Loads and processes the time-series data for the trading simulation.

    Args:
        file_path (str): The path to the 1-minute data CSV file.
                         Expected columns: 'time', 'open', 'high', 'low', 'close', 'real_volume'.

    Returns:
        dict: A dictionary of pandas DataFrames, with keys for each timeframe
              ('M1', 'M15', 'H1', 'H4', 'D1', 'W1'). Returns None if the file
              cannot be loaded or processed.
    """
    print(f"Loading data from '{file_path}'...")
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'")
        return None

    try:
        # Load the data, specifying the 'time' column as the index and parsing it as dates.
        df_m1 = pd.read_csv(
            file_path,
            index_col='time',
            parse_dates=['time']
        )

        # Standardize the volume column name
        if 'real_volume' in df_m1.columns:
            df_m1.rename(columns={'real_volume': 'volume'}, inplace=True)
        elif 'tick_volume' in df_m1.columns and 'volume' not in df_m1.columns:
            df_m1.rename(columns={'tick_volume': 'volume'}, inplace=True)
        else:
            if 'volume' not in df_m1.columns:
                print("Warning: No 'real_volume' or 'tick_volume' column found. Using 0 for volume.")
                df_m1['volume'] = 0

        print("Data loaded successfully. Resampling to higher timeframes...")

        # Define the aggregation logic for resampling OHLCV data
        ohlc_agg = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # Resample to all required timeframes
        df_m15 = df_m1.resample('15min', label='right', closed='right').agg(ohlc_agg).dropna()
        df_h1 = df_m1.resample('1h', label='right', closed='right').agg(ohlc_agg).dropna()
        df_h4 = df_m1.resample('4h', label='right', closed='right').agg(ohlc_agg).dropna()
        df_d1 = df_m1.resample('D', label='right', closed='right').agg(ohlc_agg).dropna()
        df_w1 = df_m1.resample('W-FRI', label='right', closed='right').agg(ohlc_agg).dropna()

        print("Resampling complete.")

        # Store all dataframes in a dictionary for easy access
        all_data = {
            'M1': df_m1,
            'M15': df_m15,
            'H1': df_h1,
            'H4': df_h4,
            'D1': df_d1,
            'W1': df_w1
        }
        
        return all_data

    except Exception as e:
        print(f"An error occurred while processing the data: {e}")
        if "cannot be parsed" in str(e):
            print("Hint: Ensure your CSV file has a 'time' column with a valid date/time format (e.g., 'YYYY-MM-DD HH:MM:SS').")
        if isinstance(e, KeyError):
             print("Hint: Ensure your CSV file has the required columns: 'time', 'open', 'high', 'low', 'close', and either 'real_volume' or 'tick_volume'.")
        return None


def get_previous_bar(df, current_time):
    """
    Gets the most recent bar from a dataframe that closed *before* the current time.
    """
    if df is None or df.empty:
        return None
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
    previous_bars = df[df.index < current_time]
    return previous_bars.iloc[-1] if not previous_bars.empty else None