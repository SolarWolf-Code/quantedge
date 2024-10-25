import json
import operator
import termcolor
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from datetime import datetime, timedelta

# Global cache for storing fetched data
symbol_cache = {}


def load_rules(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def get_price_data_as_dataframe(symbol):
    # print(f"Fetching data for symbol: {symbol}...")
    current_time = datetime.now()
    
    # Check if the symbol is in the cache and if the data is less than 1 hour old
    if symbol in symbol_cache:
        cached_time, df = symbol_cache[symbol]
        if current_time - cached_time < timedelta(minutes=5):
            # print(f"Using cached data for symbol: {symbol}")
            return df

    # If not in cache or data is old, fetch new data
    df = yf.download(symbol, progress=False)
    if df.empty:
        raise ValueError(f"No data found for symbol: {symbol}")
    
    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}, inplace=True)

    # Store in cache
    symbol_cache[symbol] = (current_time, df)

    return df

# Define your functions here
def rsi(symbol, period):
    # Assuming you have a way to get price data for the symbol
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.rsi(length=period).iloc[-1]
    return result['close']

def ema(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.ema(length=period).iloc[-1]
    return result['close']

def macd(symbol, fast_period, slow_period, signal_period):
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.macd(fast=fast_period, slow=slow_period, signal=signal_period).iloc[-1]['close'].iloc[0]
    return result
    
def sma_price(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.sma(length=period).iloc[-1]['close'].iloc[0]
    return result

def bollinger_bands(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.bbands(length=period).iloc[-1]['close'].iloc[0]
    print(f"Bollinger Bands for {symbol}: {result}")
    return result  # Return lower band for comparison

def fibonacci_retracement(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    high = df['high'].rolling(window=period).max().iloc[-1]
    low = df['low'].rolling(window=period).min().iloc[-1]
    current = df['close'].iloc[-1]
    retracement = ((high - current) / (high - low)).iloc[0]
    return retracement

def adx(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.adx(length=period).iloc[-1]['close'].iloc[0]
    return result

def standard_deviation_price(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    result = df['close'].rolling(window=period).std().iloc[-1].iloc[0]
    return result

def stochastic_oscillator(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    result = df.ta.stoch(k=period, d=3, smooth_k=3).iloc[-1]['close'].iloc[0]
    return result

def compare(value1, op, value2):
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne
    }
    if isinstance(value1, pd.Series):
        result = ops[op](value1, value2).all()
    else:
        result = ops[op](value1, value2)
    return result

def buy_weighted(weights: dict):
    total_weight = sum(weights.values())
    if total_weight != 1.0:
        raise ValueError("Total weight must be 1!")

    buy_string = ""
    for symbol, weight in weights.items():
        percentage = (weight / total_weight) * 100
        buy_string += f"{termcolor.colored(symbol, 'magenta')} {percentage:.2f}% "
    print(f"{termcolor.colored('Buying', 'green')} {buy_string}")

def buy_equal(symbols):
    percentage = 100 / len(symbols)

    buy_string = ""
    # check if there is only one symbol
    if len(symbols) == 1:
        buy_string = f"{termcolor.colored(symbols[0][0], 'magenta')} {percentage:.2f}% "
    else:
        for symbol in symbols:
            buy_string += f"{termcolor.colored(symbol, 'magenta')} {percentage:.2f}% "
    print(f"{termcolor.colored('Buying', 'green')} {buy_string}")

def sma_return(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    returns = df['close'].pct_change()
    result = returns.rolling(window=period).mean().iloc[-1].iloc[0]
    print(f"SMA return for {symbol}: {result}")
    return result

def standard_deviation_return(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    returns = df['close'].pct_change()
    result = returns.rolling(window=period).std().iloc[-1].iloc[0]
    print(f"Standard deviation return for {symbol}: {result}")
    return result

def max_drawdown(symbol, period=None):
    df = get_price_data_as_dataframe(symbol)
    if period is None:
        period = len(df)
    window = df['close'].rolling(window=period)
    max_in_window = window.max()
    result = ((df['close'] - max_in_window) / max_in_window).min().iloc[-1]
    print(f"Max drawdown for {symbol}: {result}")
    return result

def current_price(symbol):
    df = get_price_data_as_dataframe(symbol)
    result = df['close'].iloc[-1].iloc[0]
    print(f"Current price for {symbol}: {result}")
    return result

def cumulative_return(symbol, period):
    df = get_price_data_as_dataframe(symbol)
    start_price = df['close'].iloc[-period]
    end_price = df['close'].iloc[-1]
    result = ((end_price - start_price) / start_price).iloc[-1]
    print(f"Cumulative return for {symbol}: {result}")
    return result

def inverse_volatility(symbols, period):
    volatilities = {}
    for symbol in symbols:
        df = get_price_data_as_dataframe(symbol)
        returns = df['close'].pct_change().dropna()
        volatility = returns.rolling(window=period).std().iloc[-1]
        if isinstance(volatility, pd.Series):
            volatility = volatility.item()
        elif isinstance(volatility, pd.DataFrame):
            volatility = volatility.iloc[0, 0]
        volatilities[symbol] = volatility

    print(f"Volatilities: {volatilities}")

    # Calculate inverse volatilities
    inverse_vols = {symbol: 1 / vol if vol != 0 and not pd.isna(vol) else 0 for symbol, vol in volatilities.items()}
    
    # Calculate weights
    total_inverse_vol = sum(inverse_vols.values())
    if total_inverse_vol == 0:
        print("Warning: All volatilities are zero or NaN. Using equal weights.")
        weights = {symbol: 1/len(symbols) for symbol in symbols}
    else:
        weights = {symbol: inv_vol / total_inverse_vol for symbol, inv_vol in inverse_vols.items()}

    return weights

def buy_inverse_volatility(symbols, period):
    weights = inverse_volatility(symbols, period)
    
    buy_string = ""
    for symbol, weight in weights.items():
        percentage = weight * 100
        buy_string += f"{termcolor.colored(symbol, 'magenta')} {percentage:.2f}% "
    
    print(f"{termcolor.colored('Buying based on inverse volatility:', 'green')} {buy_string}")
    return weights

def buy_volatility(symbols, period, inverse=True):
    weights = volatility_weighting(symbols, period, inverse)
    
    buy_string = ""
    for symbol, weight in weights.items():
        percentage = weight * 100
        buy_string += f"{termcolor.colored(symbol, 'magenta')} {percentage:.2f}% "
    
    volatility_type = "inverse volatility" if inverse else "volatility"
    print(f"{termcolor.colored(f'Buying based on {volatility_type}:', 'green')} {buy_string}")
    return weights

def volatility_weighting(symbols, period, inverse=True):
    volatilities = {}
    for symbol in symbols:
        df = get_price_data_as_dataframe(symbol)
        returns = df['close'].pct_change().dropna()
        volatility = returns.rolling(window=period).std().iloc[-1]
        if isinstance(volatility, pd.Series):
            volatility = volatility.item()
        elif isinstance(volatility, pd.DataFrame):
            volatility = volatility.iloc[0, 0]
        volatilities[symbol] = volatility

    print(f"Volatilities: {volatilities}")

    if inverse:
        # Calculate inverse volatilities
        vols = {symbol: 1 / vol if vol != 0 and not pd.isna(vol) else 0 for symbol, vol in volatilities.items()}
    else:
        # Use volatilities directly
        vols = volatilities

    # Calculate weights
    total_vol = sum(vols.values())
    if total_vol == 0:
        print("Warning: All volatilities are zero or NaN. Using equal weights.")
        weights = {symbol: 1/len(symbols) for symbol in symbols}
    else:
        weights = {symbol: vol / total_vol for symbol, vol in vols.items()}

    return weights

# TODO: we also need stuff like filters. for example top x amount of stocks which could be inside a weight rule

# Function dispatcher
function_map = {
    'adx': adx,
    'bollinger_bands': bollinger_bands,
    'buy_weighted': buy_weighted,
    'buy_equal': buy_equal,
    'compare': compare,
    'cumulative_return': cumulative_return,
    'current_price': current_price,
    'ema': ema,
    'fibonacci_retracement': fibonacci_retracement,
    # 'ichimoku': ichimoku,
    'macd': macd,
    'max_drawdown': max_drawdown,
    'rsi': rsi,
    'sma_price': sma_price,
    'sma_return': sma_return,
    'standard_deviation_price': standard_deviation_price,
    'standard_deviation_return': standard_deviation_return,
    'stochastic_oscillator': stochastic_oscillator,
    'buy_volatility': buy_volatility,
}

def execute_function(func_data):
    if isinstance(func_data, dict):
        func_name = func_data['function']
        if func_name not in function_map:
            raise ValueError(f"Function {func_name} not found")
        
        func = function_map[func_name]
        
        args = [execute_function(arg) for arg in func_data['args']]
        
        print(f"Executing: {termcolor.colored(func_name, 'yellow')}")
        result = func(*args)
        return result
    return func_data

def evaluate_condition(condition):
    if condition == "else":
        return True
    return execute_function(condition)

def run_trading_system(rules):
    for i, rule in enumerate(rules['rules'], 1):
        print(f"\nEvaluating rule {i}:")
        if evaluate_condition(rule['condition']):
            print(f"Condition met for rule {i}. Executing action:")
            execute_function(rule['action'])
            break  # Exit after first matching condition
        else:
            print(f"Condition not met for rule {i}. Moving to next rule.")
    else:
        print("No conditions were met. No actions taken.")

# Usage
rules = load_rules('rules.json')
run_trading_system(rules)
