import json
from indicators import *
from utils import compare
from buy_strategies import *
from termcolor import colored

indicator_map = {
    'cumulative_return': cumulative_return,
    'rsi': rsi,
    'sma_price': sma_price,
    'macd': macd,
    'ema': ema,
    'fibonacci': fibonacci_retracement,
}

def evaluate_indicator(indicator_data):
    """Evaluate an indicator and return its value"""
    name = indicator_data['name']
    params = indicator_data['params']
    symbol = indicator_data['symbol']
    
    if name not in indicator_map:
        raise ValueError(f"Indicator {name} not found")
    
    indicator_func = indicator_map[name]
    print(f"Calculating: {colored(name, 'yellow')} for {colored(symbol, 'cyan')} with params {colored(params, 'green')}")
    
    return indicator_func(symbol, *params)

def evaluate_condition(condition):
    """Evaluate a condition node and return True/False"""
    indicator_value = evaluate_indicator(condition['indicator'])
    comparator = condition['comparator']
    target_value = condition['value']
    
    print(f"Comparing {colored(indicator_value, 'yellow')} {colored(comparator, 'red')} {colored(target_value, 'yellow')}")
    
    if comparator == '<':
        return indicator_value < target_value
    elif comparator == '>':
        return indicator_value > target_value
    elif comparator == '==':
        return indicator_value == target_value
    elif comparator == '>=':
        return indicator_value >= target_value
    elif comparator == '<=':
        return indicator_value <= target_value
    else:
        raise ValueError(f"Unknown comparator: {comparator}")

def execute_weight_action(node):
    print(f"Executing weight action: {colored(node['weight_type'], 'green')}")
    assets = node['assets']
    
    if node['weight_type'] == 'weighted':
        # For weighted type, show symbol: weight pairs
        print(f"Assets: {colored({asset['symbol']: asset['weight'] for asset in assets}, 'cyan')}")
    else:
        # For equal type, just show the symbols
        print(f"Assets: {colored([asset['symbol'] for asset in assets], 'cyan')}")
    if node['weight_type'] == 'equal':
        return buy_equal(assets)
    else:  # specified
        return buy_weighted(assets)

def process_node(node):
    """Process a node in the decision tree"""
    if not isinstance(node, dict):
        return
        
    node_type = node.get('type')
    
    if node_type == 'condition':
        condition_result = evaluate_condition(node)
        
        if condition_result:
            print(colored("Condition is True, taking true branch", 'green'))
            if node['if_true']:
                process_node(node['if_true'][0])
        else:
            print(colored("Condition is False, taking false branch", 'red'))
            if node['if_false']:
                process_node(node['if_false'][0])
                
    elif node_type == 'weight':
        execute_weight_action(node)
    else:
        raise ValueError(f"Unknown node type: {node_type}")

def run_trading_system(rules):
    """Run the trading system with the given rules"""
    print(colored(f"\nExecuting strategy: {rules['name']}", 'blue', attrs=['bold']))
    print(colored("=" * 50, 'blue'))
    
    try:
        process_node(rules['rules'])
    except Exception as e:
        print(colored(f"Error executing strategy: {str(e)}", 'red'))
        raise

def load_rules(file_path):
    """Load rules from a JSON file"""
    try:
        with open(file_path, 'r') as file:
            rules = json.load(file)
            print(colored(f"Successfully loaded rules from {file_path}", 'green'))
            return rules
    except Exception as e:
        print(colored(f"Error loading rules from {file_path}: {str(e)}", 'red'))
        raise
