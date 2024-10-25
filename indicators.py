import pandas as pd
import pandas_ta as ta
from data_fetcher import load_historical_data
from datetime import datetime, timedelta

def rsi(symbol, period):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=period * 2)
    df = load_historical_data(symbol, start_date, end_date)
    result = df.ta.rsi(length=period).iloc[-1]
    if isinstance(result, pd.Series):
        return float(result.iloc[0])
    return float(result)

def ema(symbol, period):
    df = load_historical_data(symbol)
    result = df.ta.ema(length=period).iloc[-1]
    return result

def macd(symbol, fast_period, slow_period, signal_period):
    df = load_historical_data(symbol)
    result = df.ta.macd(fast=fast_period, slow=slow_period, signal=signal_period).iloc[-1].iloc[0]
    return result

def sma_price(symbol, period):
    df = load_historical_data(symbol)
    result = df.ta.sma(length=period).iloc[-1]
    print(symbol, result)
    return result

def fibonacci_retracement(symbol, period):
    df = load_historical_data(symbol)
    high = df['high'].rolling(window=period).max().iloc[-1]
    low = df['low'].rolling(window=period).min().iloc[-1]
    current = df['close'].iloc[-1]
    retracement = ((high - current) / (high - low))
    return retracement

def adx(symbol, period):
    df = load_historical_data(symbol)
    result = df.ta.adx(length=period).iloc[-1].iloc[0]
    return result

def standard_deviation_price(symbol, period):
    df = load_historical_data(symbol)
    result = df['close'].rolling(window=period).std().iloc[-1]
    return result

def stochastic_oscillator(symbol, period):
    df = load_historical_data(symbol)
    result = df.ta.stoch(k=period, d=3, smooth_k=3).iloc[-1].iloc[0]
    return result

def sma_return(symbol, period):
    df = load_historical_data(symbol)
    returns = df['close'].pct_change()
    result = returns.rolling(window=period).mean().iloc[-1]
    return result

def standard_deviation_return(symbol, period):
    df = load_historical_data(symbol)
    returns = df['close'].pct_change()
    result = returns.rolling(window=period).std().iloc[-1]
    return result

def max_drawdown(symbol, period=None):
    df = load_historical_data(symbol)
    if period is None:
        period = len(df)
    window = df['close'].rolling(window=period)
    max_in_window = window.max()
    result = ((df['close'] - max_in_window) / max_in_window).min()
    return result

def current_price(symbol):
    df = load_historical_data(symbol)
    result = df['close'].iloc[-1]
    return result

def cumulative_return(symbol, period):
    df = load_historical_data(symbol)
    start_price = df['close'].iloc[-period]
    end_price = df['close'].iloc[-1]
    result = ((end_price - start_price) / start_price)
    return result
