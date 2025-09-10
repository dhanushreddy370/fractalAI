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
                print("Warning: No volume column found. Using 0 for volume.")
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
             print("Hint: Ensure your CSV file has the required columns: 'time', 'open', 'high', 'low', 'close'.")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    DATA_FILE = "EURUSD1m6months.csv"

    if not os.path.exists(DATA_FILE):
        print(f"File '{DATA_FILE}' not found.")
        print("Please place your data file in the same directory as this script,")
        print(f"or update the 'DATA_FILE' variable above.")
        with open(DATA_FILE, 'w') as f:
            f.write("time,open,high,low,close,tick_volume,spread,real_volume\n")
            f.write("2024-07-10 00:00:00,1.082,1.082,1.08191,1.08192,0,4,0\n")
        print(f"A sample file '{DATA_FILE}' has been created with the correct format.")
    else:
        data_frames = load_and_prepare_data(DATA_FILE)

        if data_frames:
            print("\n--- Data Verification ---")
            for timeframe, df in data_frames.items():
                print(f"Timeframe: {timeframe} | Shape: {df.shape} | Last 2 rows:")
                print(df.tail(2))
                print("-" * 50)