import json
from indicators import *
from utils import compare
from data_fetcher import get_earliest_date
from buy_strategies import *
from termcolor import colored

indicator_map = {
    'cumulative_return': cumulative_return,
    # 'rsi': rsi,
    'sma_price': sma_price,
    'macd': macd,
    'ema': ema,
    'fibonacci': fibonacci_retracement,
}

def evaluate_indicator(indicator_data, end_date):
    """Evaluate an indicator and return its value"""
    name = indicator_data['name']
    params = indicator_data['params']
    symbol = indicator_data['symbol']
    
    # Check earliest available date
    earliest_date = get_earliest_date(symbol)
    if earliest_date is None or earliest_date > end_date.date():
        print(f"{colored('Skipping', 'red')} {colored(symbol, 'cyan')} - data not available before {colored(end_date, 'yellow')}")
        return None
    
    if name not in indicator_map:
        raise ValueError(f"Indicator {name} not found")
    
    indicator_func = indicator_map[name]
    print(f"Calculating: {colored(name, 'yellow')} for {colored(symbol, 'cyan')} with params {colored(params, 'green')}")
    
    return indicator_func(symbol, end_date, *params)

def evaluate_condition(condition, end_date):
    """Evaluate a condition node and return True/False"""
    indicator_value = evaluate_indicator(condition['indicator'], end_date)
    
    # Skip condition if indicator value is None (data not available)
    if indicator_value is None:
        print(colored("Skipping condition due to unavailable data", 'red'))
        return False
        
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

def execute_weight_action(node, end_date, purchases):
    print(f"Executing weight action: {colored(node['weight_type'], 'green')}")
    assets = node['assets']
    
    # Filter out assets that don't have data for the required period
    valid_assets = []
    for asset in assets:
        earliest_date = get_earliest_date(asset['symbol'])
        if earliest_date is None or earliest_date > end_date.date():
            print(f"{colored('Skipping', 'red')} {colored(asset['symbol'], 'cyan')} - data not available before {colored(end_date.date(), 'yellow')}")
            continue
        valid_assets.append(asset)
    
    if not valid_assets:
        print(colored("No valid assets found with available data - skipping weight action", 'red'))
        return
    
    # Recalculate weights for valid assets only
    if node['weight_type'] == 'weighted':
        # Get total weight of valid assets
        total_weight = sum(asset['weight'] for asset in valid_assets)
        # Normalize weights
        for asset in valid_assets:
            asset['weight'] = asset['weight'] / total_weight
        print(f"Assets: {colored({asset['symbol']: asset['weight'] for asset in valid_assets}, 'cyan')}")
    else:
        print(f"Assets: {colored([asset['symbol'] for asset in valid_assets], 'cyan')}")
    
    if node['weight_type'] == 'equal':
        return buy_equal(valid_assets, purchases)
    else:  # specified
        return buy_weighted(valid_assets, purchases)

def process_node(node, end_date, purchases):
    """Process a node in the decision tree"""
    if not isinstance(node, dict):
        return
        
    node_type = node.get('type')
    
    if node_type == 'condition':
        condition_result = evaluate_condition(node, end_date)
        
        if condition_result:
            print(colored("Condition is True, taking true branch", 'green'))
            if node['if_true']:
                process_node(node['if_true'][0], end_date, purchases)
        else:
            print(colored("Condition is False, taking false branch", 'red'))
            if node['if_false']:
                process_node(node['if_false'][0], end_date, purchases)
                
    elif node_type == 'weight':
        execute_weight_action(node, end_date, purchases)  # Added end_date parameter
    else:
        raise ValueError(f"Unknown node type: {node_type}")

def run_trading_system(rules, end_date):
    """Run the trading system with the given rules"""
    print(colored(f"\nExecuting strategy: {rules['name']}", 'blue', attrs=['bold']))
    print(colored("=" * 50, 'blue'))
    
    purchases = {}

    try:
        process_node(rules['rules'], end_date, purchases)
    except Exception as e:
        print(colored(f"Error executing strategy: {str(e)}", 'red'))
        raise


    return purchases

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
