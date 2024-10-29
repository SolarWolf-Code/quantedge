import pandas as pd
import pandas_ta as ta
from data_fetcher import load_historical_data

# def rsi(symbol, start_date, period):
#     end_date = datetime.now().date()
#     start_date = end_date - timedelta(days=period * 2)
#     df = load_historical_data(symbol, start_date, end_date)
#     result = df.ta.rsi(length=period).iloc[-1]
#     if isinstance(result, pd.Series):
#         return float(result.iloc[0])
#     return float(result)

def ema(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} EMA calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    result = df.ta.ema(length=period).iloc[-1]
    return result

def macd(symbol, end_date, fast_period, slow_period, signal_period):
    df = load_historical_data(symbol, end_date)
    if len(df) < max(fast_period, slow_period, signal_period):
        print(f"Warning: Not enough data points for {symbol} MACD calculation. Need {max(fast_period, slow_period, signal_period)} days, but only have {len(df)}. Skipping...")
        return None
    result = df.ta.macd(fast=fast_period, slow=slow_period, signal=signal_period).iloc[-1].iloc[0]
    return result

def sma_price(symbol, end_date, period):
    print(f"Calculating SMA for {symbol} with period {period} and end date {end_date}")
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} SMA price calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    result = df.ta.sma(length=period).iloc[-1]
    return result

def fibonacci_retracement(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} fibonacci retracement calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    high = df['high'].rolling(window=period).max().iloc[-1]
    low = df['low'].rolling(window=period).min().iloc[-1]
    current = df['close'].iloc[-1]
    retracement = ((high - current) / (high - low))
    return retracement

def adx(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} ADX calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    result = df.ta.adx(length=period).iloc[-1].iloc[0]
    return result

def standard_deviation_price(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} standard deviation price calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    result = df['close'].rolling(window=period).std().iloc[-1]
    return result

def stochastic_oscillator(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} stochastic oscillator calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    result = df.ta.stoch(k=period, d=3, smooth_k=3).iloc[-1].iloc[0]
    return result

def sma_return(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} SMA return calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    returns = df['close'].pct_change()
    result = returns.rolling(window=period).mean().iloc[-1]
    return result

def standard_deviation_return(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} standard deviation return calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    returns = df['close'].pct_change()
    result = returns.rolling(window=period).std().iloc[-1]
    return result

def max_drawdown(symbol, end_date, period=None):
    df = load_historical_data(symbol, end_date)
    if period is None:
        period = len(df)
    
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} max drawdown calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None

    window = df['close'].rolling(window=period)
    max_in_window = window.max()
    result = ((df['close'] - max_in_window) / max_in_window).min()
    return result

def current_price(symbol, end_date):
    df = load_historical_data(symbol, end_date)
    result = df['close'].iloc[-1]
    return result

def cumulative_return(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    # Skip calculation if we don't have enough data points
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} cumulative return calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    
    start_price = df['close'].iloc[-period]
    end_price = df['close'].iloc[-1]
    result = ((end_price - start_price) / start_price)
    return result
