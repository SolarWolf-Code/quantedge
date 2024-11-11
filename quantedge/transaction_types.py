def buy_weighted(assets, transactions):
    """
    Buy assets with specified weights
    assets: list of dicts, each with 'symbol' and 'weight' keys
    """
    # Convert list of assets to dict of symbol: weight
    weights = {asset['symbol']: asset['weight'] for asset in assets}
    
    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 1e-6:  # Allow for small floating-point errors
        raise ValueError(f"Total weight must be 1! Current total: {total_weight}")

    for symbol, weight in weights.items():
        percentage = weight
        transactions['buy'][symbol] = percentage
    

def buy_equal(assets, transactions):
    """
    Buy assets with equal weights
    assets: list of dicts, each with 'symbol' key
    """
    symbols = [asset['symbol'] for asset in assets]
    percentage = 100 / len(symbols)

    for symbol in symbols:
        transactions['buy'][symbol] = percentage / 100

def sell_all(assets, transactions):
    for asset in assets:
        transactions['sell'][asset['symbol']] = 1.0

def sell_partial(assets, transactions):
    for asset in assets:
        transactions['sell'][asset['symbol']] = asset['percentage']

