import json
from indicators import *
from utils import compare, select_tickers
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
    'select_tickers': select_tickers,
}

def execute_function(func_data):
    if isinstance(func_data, dict):
        if 'utility' in func_data:
            func_name = func_data['utility']
            if func_name not in function_map:
                raise ValueError(f"Function {func_name} not found")
            
            func = function_map[func_name]
            
            args = [execute_function(arg) for arg in func_data.get('args', [])]
            
            print(f"Executing: {colored(func_name, 'yellow')}")
            result = func(*args)
            return result
        elif 'indicator' in func_data:
            # For indicators, we don't execute them here, just return the dict
            return func_data
        elif 'type' in func_data:
            func_name = func_data['type']
            if func_name not in function_map:
                raise ValueError(f"Function {func_name} not found")
            
            func = function_map[func_name]
            
            args = [execute_function(arg) for arg in func_data.get('args', [])]
            
            print(f"Executing: {colored(func_name, 'yellow')}")
            result = func(*args)
            return result
        else:
            return func_data
    elif isinstance(func_data, list):
        return [execute_function(item) for item in func_data]
    return func_data

def evaluate_feature(feature):
    return execute_function(feature)

def run_trading_system(rules):
    def process_node(node):
        if 'feature' in node:
            condition = evaluate_feature(node['feature'])
            if condition:
                if 'left' in node:
                    process_node(node['left'])
                else:
                    execute_function(node['action'])
            else:
                if 'right' in node:
                    process_node(node['right'])
                else:
                    execute_function(node['action'])
        else:
            execute_function(node['action'])

    process_node(rules)

def load_rules(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)
