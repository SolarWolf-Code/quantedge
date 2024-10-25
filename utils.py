import operator
import pandas as pd
from indicators import *

def evaluate_indicator(indicator_dict):
    if isinstance(indicator_dict, dict) and 'indicator' in indicator_dict:
        func = globals()[indicator_dict['indicator']]
        args = indicator_dict.get('args', [])
        return func(*args)
    return indicator_dict

def compare(value1, op, value2):
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne
    }
    
    # Evaluate indicators if they are dictionaries
    value1 = evaluate_indicator(value1)
    value2 = evaluate_indicator(value2)
    
    if isinstance(value1, pd.Series):
        result = ops[op](value1, value2).all()
    else:
        result = ops[op](value1, value2)
    return result

def select_tickers(symbols, indicator_func, indicator_args, top_n, ascending=False):
    """
    Select top or bottom N tickers based on a given indicator.
    
    :param symbols: List of ticker symbols
    :param indicator_func: Dictionary containing indicator function info
    :param indicator_args: Arguments for the indicator function (excluding the symbol)
    :param top_n: Number of tickers to select
    :param ascending: If True, select bottom N. If False, select top N.
    :return: List of selected ticker symbols
    """
    results = []
    for symbol in symbols:
        try:
            if isinstance(indicator_func, dict) and 'indicator' in indicator_func:
                func = globals()[indicator_func['indicator']]
            else:
                raise ValueError(f"Invalid indicator function: {indicator_func}")
            
            value = func(symbol, *indicator_args)
            results.append((symbol, value))
        except Exception as e:
            print(f"Error calculating indicator for {symbol}: {e}")
    
    sorted_results = sorted(results, key=lambda x: x[1], reverse=not ascending)
    selected_tickers = [ticker for ticker, _ in sorted_results[:top_n]]
    
    return selected_tickers

def replace_symbol_in_feature(feature, symbol):
    if isinstance(feature, dict):
        return {k: replace_symbol_in_feature(v, symbol) for k, v in feature.items()}
    elif isinstance(feature, list):
        return [replace_symbol_in_feature(item, symbol) for item in feature]
    elif feature == "SYMBOL":
        return symbol
    else:
        return feature