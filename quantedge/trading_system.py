import json
from indicators import *
from data_fetcher import get_earliest_date
from transaction_types import *
from termcolor import colored
import operator

indicator_map = {
    'cumulative_return': cumulative_return,
    'sma_price': sma_price,
    'rsi': rsi,
    'macd': macd,
    'ema': ema,
    # 'fibonacci': fibonacci_retracement,
    'atr': atr,
    'atr_percent': atr_percent,
    'vix': vix,
    'vix_change': vix_change,
    'sma_cross': sma_cross,
}

def evaluate_indicator(indicator_data, end_date):
    """Evaluate an indicator and return its value"""
    name = indicator_data['name']
    params = indicator_data['params']
    
    # Special handling for composite indicators
    if name == 'and':
        if 'inputs' not in indicator_data:
            raise ValueError("'and' indicator requires 'inputs' field")
        
        results = []
        for input_indicator in indicator_data['inputs']:
            result = evaluate_indicator(input_indicator, end_date)
            if result is None:
                return None
            results.append(result)
        return results
    
    # Regular indicator processing
    if 'symbol' not in indicator_data:
        raise ValueError(f"Indicator {name} missing required 'symbol' field")
    
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
    """Evaluate a condition and return True or False"""
    indicator_value = evaluate_indicator(condition['indicator'], end_date)
    if indicator_value is None:
        return None
        
    comparator = condition['comparator']
    threshold = condition['value']
    
    # Handle composite indicator results
    if isinstance(indicator_value, list):
        if isinstance(threshold, list):
            # Multiple thresholds for multiple values
            if len(indicator_value) != len(threshold):
                raise ValueError("Mismatched number of values for composite indicator comparison")
            results = []
            for val, thresh in zip(indicator_value, threshold):
                results.append(compare_values(val, thresh, comparator))
            return all(results)  # For 'and' indicator, all conditions must be true
        else:
            # Single threshold for all values
            results = []
            for val in indicator_value:
                results.append(compare_values(val, threshold, comparator))
            return all(results)
        
    return compare_values(indicator_value, threshold, comparator)

def compare_values(value, threshold, comparator):
    """Compare a single value against a threshold using the given comparator"""
    if value is None:
        return None
        
    ops = {
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne
    }
    
    return ops[comparator](value, threshold)

def execute_weight_action(node, end_date, transactions):
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
    
    # for buying
    if node['weight_type'].endswith('buy'):
        # Recalculate weights for valid assets only
        if node['weight_type'] == 'weighted_buy':
            # Get total weight of valid assets
            total_weight = sum(asset['weight'] for asset in valid_assets)
            # Normalize weights
            for asset in valid_assets:
                asset['weight'] = asset['weight'] / total_weight
            print(f"Assets: {colored({asset['symbol']: asset['weight'] for asset in valid_assets}, 'cyan')}")
        else:
            print(f"Assets: {colored([asset['symbol'] for asset in valid_assets], 'cyan')}")
        
        if node['weight_type'] == 'equal_buy':
            return buy_equal(valid_assets, transactions)
        elif node['weight_type'] == 'weighted_buy':
            return buy_weighted(valid_assets, transactions)
        else:
            raise ValueError(f"Unknown weight type: {node['weight_type']}")
        
    elif node['weight_type'].endswith('sell'):
        if node['weight_type'] == 'all_sell':
            return sell_all(valid_assets, transactions)
        elif node['weight_type'] == 'partial_sell':
            return sell_partial(valid_assets, transactions)
        else:
            raise ValueError(f"Unknown weight type: {node['weight_type']}")
    else:
        raise ValueError(f"Unknown weight type: {node['weight_type']}")

def process_node(node, end_date, transactions):
    """Process a node in the decision tree"""
    if not isinstance(node, dict):
        return
        
    node_type = node.get('type')
    
    if node_type == 'condition':
        condition_result = evaluate_condition(node, end_date)
        
        if condition_result:
            print(colored("Condition is True, taking true branch", 'green'))
            # Process all actions in the true branch
            if node['if_true']:
                for action in node['if_true']:
                    process_node(action, end_date, transactions)
        else:
            print(colored("Condition is False, taking false branch", 'red'))
            # Process all actions in the false branch
            if node['if_false']:
                for action in node['if_false']:
                    process_node(action, end_date, transactions)
                
    elif node_type == 'weight':
        execute_weight_action(node, end_date, transactions)
    else:
        raise ValueError(f"Unknown node type: {node_type}")

def run_trading_system(rules, end_date):
    """Run the trading system with the given rules"""
    print(colored(f"\nExecuting strategy: {rules['name']}", 'blue', attrs=['bold']))
    print(colored("=" * 50, 'blue'))
    
    transactions = {
        'buy': {},
        'sell': {}
    }

    try:
        process_node(rules['rules'], end_date, transactions)
    except Exception as e:
        print(colored(f"Error executing strategy: {str(e)}", 'red'))
        raise


    return transactions

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
