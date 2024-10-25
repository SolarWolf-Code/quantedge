from trading_system import load_rules, run_trading_system
import time

if __name__ == "__main__":
    start_time = time.time()
    rules = load_rules('rules.json')
    run_trading_system(rules)
    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
