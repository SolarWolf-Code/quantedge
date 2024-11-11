import pandas as pd
import pandas_ta as ta
from quantedge.data_fetcher import load_historical_data

def rsi(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} RSI calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None

    result = df.ta.rsi(length=period).iloc[-1]
    return result

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
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} SMA price calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    result = df.ta.sma(length=period).iloc[-1]
    return result

# def fibonacci_retracement(symbol, end_date, period):
#     df = load_historical_data(symbol, end_date)
#     if len(df) < period:
#         print(f"Warning: Not enough data points for {symbol} fibonacci retracement calculation. Need {period} days, but only have {len(df)}. Skipping...")
#         return None
#     high = df['high'].rolling(window=period).max().iloc[-1]
#     low = df['low'].rolling(window=period).min().iloc[-1]
#     current = float(df['close'].iloc[-1])
#     retracement = ((high - current) / (high - low))
#     return retracement

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
    
    # convert to float
    df['close'] = df['close'].astype(float)

    result = df.ta.stoch(k=period, d=3, smooth_k=3).iloc[-1].iloc[0] # this is fast OSC
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

def atr(symbol, end_date, period):
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} ATR calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None

    # convert open, high, low, close to float
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    
    result = df.ta.atr(length=period).iloc[-1]
    return result

def atr_percent(symbol, end_date, period):
    """
    Calculate ATR as a percentage of price to normalize across different price levels
    """
    df = load_historical_data(symbol, end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for {symbol} ATR percent calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    
    # convert open, high, low, close to float
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)

    # Calculate ATR
    atr_value = df.ta.atr(length=period)
    # Get current price
    current_price = df['close']
    # Calculate ATR as percentage of price
    atr_pct = (atr_value / current_price)
    
    return atr_pct.iloc[-1]

def vix(symbol, end_date, period=None):
    """
    Get the VIX value for a given date. If period is specified, returns the average over that period.
    """
    df = load_historical_data('^VIX', end_date)
    if period:
        if len(df) < period:
            print(f"Warning: Not enough data points for VIX calculation. Need {period} days, but only have {len(df)}. Skipping...")
            return None
        result = df['close'].rolling(window=period).mean().iloc[-1]
    else:
        result = df['close'].iloc[-1]
    
    return result

def vix_change(symbol, end_date, period):
    """
    Calculate how much VIX has changed over the last N days
    Returns the absolute point change in VIX
    """
    df = load_historical_data('^VIX', end_date)
    if len(df) < period:
        print(f"Warning: Not enough data points for VIX change calculation. Need {period} days, but only have {len(df)}. Skipping...")
        return None
    
    current_vix = df['close'].iloc[-1]
    past_vix = df['close'].iloc[-period]
    return float(current_vix - past_vix)

def sma_cross(symbol, end_date, fast_period, slow_period):
    """
    Calculate if fast SMA is above slow SMA
    Returns the ratio of fast SMA to slow SMA
    """
    df = load_historical_data(symbol, end_date)
    if len(df) < max(fast_period, slow_period):
        print(f"Warning: Not enough data points for {symbol} SMA cross calculation. Need {max(fast_period, slow_period)} days, but only have {len(df)}. Skipping...")
        return None
    
    fast_sma = df['close'].rolling(window=fast_period).mean()
    slow_sma = df['close'].rolling(window=slow_period).mean()
    
    # Return ratio of fast to slow SMA (> 1 means bullish, < 1 means bearish)
    return (fast_sma / slow_sma).iloc[-1]
