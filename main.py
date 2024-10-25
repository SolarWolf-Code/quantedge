from trading_system import load_rules, run_trading_system

if __name__ == "__main__":
    rules = load_rules('rules.json')
    run_trading_system(rules)
