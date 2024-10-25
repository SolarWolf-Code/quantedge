import termcolor
from data_fetcher import load_historical_data
import pandas as pd

def buy_weighted(weights):
    if isinstance(weights, list) and len(weights) == 1 and isinstance(weights[0], dict):
        weights = weights[0]
    
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-6:  # Allow for small floating-point errors
        raise ValueError(f"Total weight must be 1! Current total: {total_weight}")

    buy_string = ""
    for symbol, weight in weights.items():
        percentage = weight * 100
        buy_string += f"{termcolor.colored(symbol, 'magenta')} {percentage:.2f}% "
    print(f"{termcolor.colored('Buying', 'green')} {buy_string}")

def buy_equal(symbols):
    percentage = 100 / len(symbols)

    buy_string = ""
    if len(symbols) == 1:
        buy_string = f"{termcolor.colored(symbols[0][0], 'magenta')} {percentage:.2f}% "
    else:
        for symbol in symbols:
            buy_string += f"{termcolor.colored(symbol, 'magenta')} {percentage:.2f}% "
    print(f"{termcolor.colored('Buying', 'green')} {buy_string}")

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
        df = load_historical_data(symbol)
        returns = df['close'].pct_change().dropna()
        volatility = returns.rolling(window=period).std().iloc[-1]
        if isinstance(volatility, pd.Series):
            volatility = volatility.item()
        elif isinstance(volatility, pd.DataFrame):
            volatility = volatility.iloc[0, 0]
        volatilities[symbol] = volatility

    if inverse:
        vols = {symbol: 1 / vol if vol != 0 and not pd.isna(vol) else 0 for symbol, vol in volatilities.items()}
    else:
        vols = volatilities

    total_vol = sum(vols.values())
    if total_vol == 0:
        print("Warning: All volatilities are zero or NaN. Using equal weights.")
        weights = {symbol: 1/len(symbols) for symbol in symbols}
    else:
        weights = {symbol: vol / total_vol for symbol, vol in vols.items()}

    return weights
