import json
from indicators import *
from utils import compare
from buy_strategies import *
from termcolor import colored

function_map = {
    'adx': adx,
    'buy_weighted': buy_weighted,
    'buy_equal': buy_equal,
    'compare': compare,
    'cumulative_return': cumulative_return,
    'current_price': current_price,
    'ema': ema,
    'fibonacci_retracement': fibonacci_retracement,
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
        if 'function' in func_data:
            func_name = func_data['function']
            if func_name not in function_map:
                raise ValueError(f"Function {func_name} not found")
            
            func = function_map[func_name]
            
            args = [execute_function(arg) for arg in func_data['args']]
            
            print(f"Executing: {colored(func_name, 'yellow')}")
            result = func(*args)
            return result
        else:
            # If it's a dictionary without a 'function' key, return it as is
            return func_data
    return func_data

def evaluate_condition(condition):
    if condition == "else":
        return True
    return execute_function(condition)

def run_trading_system(rules):
    for i, rule in enumerate(rules['rules'], 1):
        if evaluate_condition(rule['condition']):
            execute_function(rule['action'])
            break  # Exit after first matching condition

def load_rules(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
