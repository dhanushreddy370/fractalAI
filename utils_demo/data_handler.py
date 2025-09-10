import pandas as pd
import os

"""
Phase 1: Foundation & Data Preparation (data_handler.py)

This module is the data backbone of the trading simulator. Its purpose is to:
1. Load raw 1-minute OHLC data from a user-provided CSV file.
2. Correctly parse the 'time' column to create a DatetimeIndex.
3. Resample the 1-minute data into all higher timeframes required by the strategy:
   - 15-minute (M15)
   - 1-hour (H1)
   - 4-hour (H4)
   - Daily (D1)
   - Weekly (W1)
4. Return a dictionary of clean, perfectly aligned pandas DataFrames.
"""

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
        # This is the key fix for the 'instance of 'Index'' error.
        df_m1 = pd.read_csv(
            file_path,
            index_col='time',
            parse_dates=['time']
        )

        # Standardize the volume column name. The strategy will expect 'volume'.
        # We prioritize 'real_volume' as it's generally more reliable.
        if 'real_volume' in df_m1.columns:
            df_m1.rename(columns={'real_volume': 'volume'}, inplace=True)
        elif 'tick_volume' in df_m1.columns and 'volume' not in df_m1.columns:
            df_m1.rename(columns={'tick_volume': 'volume'}, inplace=True)
        else:
            # If no volume column is found, create a dummy one to prevent errors.
            if 'volume' not in df_m1.columns:
                print("Warning: No 'real_volume' or 'tick_volume' column found. Using 0 for volume.")
                df_m1['volume'] = 0


        # --- TIMEZONE CONVERSION REMOVED AS PER USER REQUEST ---
        # The script now assumes the 'time' column in the CSV is already in the desired timezone (EST).

        print("Data loaded successfully. Resampling to higher timeframes...")

        # Define the aggregation logic for resampling OHLCV data
        ohlc_agg = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }

        # Resample to all required timeframes. This will now work correctly.
        # The 'label' and 'closed' parameters ensure the timestamp of the resampled
        # bar is at the end of the period, which is standard practice.
        df_m15 = df_m1.resample('15min', label='right', closed='right').agg(ohlc_agg).dropna()
        df_h1 = df_m1.resample('1h', label='right', closed='right').agg(ohlc_agg).dropna()
        df_h4 = df_m1.resample('4h', label='right', closed='right').agg(ohlc_agg).dropna()
        df_d1 = df_m1.resample('D', label='right', closed='right').agg(ohlc_agg).dropna()
        # For weekly data, 'W-FRI' means each week ends on Friday's close.
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

# --- Example Usage ---
if __name__ == "__main__":
    # --- IMPORTANT ---
    # Set the path to your 1-minute data file here.
    # The CSV should have columns: 'time', 'open', 'high', 'low', 'close', 'real_volume' etc.
    DATA_FILE = "EURUSD1m6months.csv"

    # Check if the user has provided their data file.
    if not os.path.exists(DATA_FILE):
        print(f"File '{DATA_FILE}' not found.")
        print("Please place your data file in the same directory as this script,")
        print(f"or update the 'DATA_FILE' variable above.")
        # Create a sample file with the correct header and one row for the user to see the format.
        with open(DATA_FILE, 'w') as f:
            f.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
            f.write("2024-07-10 00:00:00,1.082,1.082,1.08191,1.08192,0,4,0\n")
        print(f"A sample file '{DATA_FILE}' has been created with the correct format.")
    else:
        # Load and process the data using our main function
        data_frames = load_and_prepare_data(DATA_FILE)

        # Verify the output
        if data_frames:
            print("\n--- Data Verification ---")
            for timeframe, df in data_frames.items():
                # Show a sample of the data to confirm it's loaded correctly
                print(f"Timeframe: {timeframe} | Shape: {df.shape} | Last 2 rows:")
                print(df.tail(2))
                print("-" * 50)
