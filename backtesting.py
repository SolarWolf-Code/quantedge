from datetime import datetime
from trading_system import load_rules, run_trading_system
from data_fetcher import load_historical_data, load_daily_values, get_earliest_date
import termcolor
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

class Portfolio:
    def __init__(self, starting_capital, monthly_investment, rules, end_date, start_date):
        self.starting_capital = starting_capital
        self.monthly_investment = monthly_investment
        self.cash = starting_capital
        self.shares = {}
        self.rules = rules
        self.end_date = end_date
        self.start_date = start_date
        self.min_cash = 5
        self.inital_start_date = start_date
        self.inital_end_date = end_date
        self.daily_values = pd.DataFrame(columns=['date', 'portfolio_value', 'cash'])
        self.daily_values.set_index('date', inplace=True)
        
        # Add daily shares tracking
        self.daily_shares = {}  # Format: {date: {symbol: shares}}
        # Modify daily_values to include shares for each symbol
        self.daily_values = pd.DataFrame(columns=['date', 'portfolio_value', 'cash'])
        self.daily_values.set_index('date', inplace=True)

    def calculate_portfolio_stats(self):
        """Calculate various portfolio performance metrics"""
        # Calculate daily returns
        self.daily_values['daily_return'] = self.daily_values['portfolio_value'].pct_change(fill_method=None)
        
        # Risk-free rate (using 2% annual as example)
        risk_free_rate = 0.02
        daily_rf_rate = (1 + risk_free_rate) ** (1/252) - 1
        
        # Calculate metrics
        stats = {
            'Total Return': self.get_total_return() * 100,
            'Annualized Return': self.get_annualized_return() * 100,
            'Max Drawdown': self.calculate_max_drawdown() * 100,
            'Volatility': self.calculate_volatility() * 100,
            'Calmar Ratio': self.calculate_calmar_ratio(),
            'Sharpe Ratio': self.calculate_sharpe_ratio(daily_rf_rate),
            'Sortino Ratio': self.calculate_sortino_ratio(daily_rf_rate),
            'Ulcer Index': self.calculate_ulcer_index(),
            'UPI': self.calculate_ulcer_performance_index(),
            'Beta': self.calculate_beta(),
        }
        
        return pd.Series(stats)
    
    def calculate_volatility(self):
        """Calculate volatility"""
        return np.sqrt(252) * self.daily_values['daily_return'].std()

    def calculate_max_drawdown(self):
        """Calculate maximum drawdown"""
        portfolio_values = self.daily_values['portfolio_value']
        rolling_max = portfolio_values.expanding().max()
        drawdowns = portfolio_values / rolling_max - 1
        return float(drawdowns.min())
    
    def calculate_beta(self):
        """Calculate beta relative to SPY (market benchmark)"""
        # Get SPY data for the same period
        spy_data = load_daily_values(('SPY',), self.inital_start_date, self.inital_end_date)
        # Convert to float type before calculations
        spy_returns = spy_data['SPY'].astype(float).pct_change(fill_method=None)
        
        # Calculate portfolio and market covariance
        portfolio_returns = self.daily_values['portfolio_value'].astype(float).pct_change(fill_method=None)
        covariance = portfolio_returns.cov(spy_returns)
        market_variance = spy_returns.var()
        
        # Calculate beta
        return covariance / market_variance if market_variance != 0 else 1.0
        
    
    def calculate_sharpe_ratio(self, daily_rf_rate):
        """Calculate Sharpe ratio"""
        excess_returns = self.daily_values['daily_return'] - daily_rf_rate
        if len(excess_returns) < 2:  # Need at least 2 points for std
            return 0
        return np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
    
    def calculate_sortino_ratio(self, daily_rf_rate):
        """Calculate Sortino ratio"""
        excess_returns = self.daily_values['daily_return'] - daily_rf_rate
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) < 2:
            return 0
        downside_std = np.sqrt(np.mean(downside_returns**2))
        return np.sqrt(252) * (excess_returns.mean() / downside_std) if downside_std != 0 else 0
    
    def calculate_calmar_ratio(self):
        """Calculate Calmar ratio"""
        max_dd = self.calculate_max_drawdown()
        if max_dd == 0:
            return 0
        return self.get_annualized_return() / abs(max_dd)
    
    def calculate_ulcer_index(self):
        """Calculate Ulcer Index"""
        portfolio_values = self.daily_values['portfolio_value']
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values / rolling_max - 1) * 100
        return np.sqrt(np.mean(drawdowns**2))
    
    def calculate_ulcer_performance_index(self):
        """Calculate Ulcer Performance Index"""
        ulcer_index = self.calculate_ulcer_index()
        if ulcer_index == 0:
            return 0
        return (self.get_annualized_return() - 0.02) / ulcer_index  # Using 2% as risk-free rate
    
    def get_total_return(self):
        """Calculate total return"""
        if len(self.daily_values) < 2:
            return 0
        first_value = self.daily_values['portfolio_value'].iloc[0]
        last_value = self.daily_values['portfolio_value'].iloc[-1]
        return (last_value / first_value) - 1

    def buy(self, symbol, price, quantity):
        cost = price * quantity
        self.cash -= cost
        self.shares[symbol] = self.shares.get(symbol, 0) + quantity
        print(f"{termcolor.colored('Bought', 'green')} {termcolor.colored(symbol, 'magenta')} {quantity:.2f} shares @ ${price:.2f}")

        # Update daily shares for the current date
        current_date = self.start_date.strftime('%Y-%m-%d')
        if current_date not in self.daily_shares:
            self.daily_shares[current_date] = {}
        self.daily_shares[current_date][symbol] = self.shares[symbol]

    def sell(self, symbol, price, quantity):
        self.cash += price * quantity
        self.shares[symbol] = self.shares.get(symbol, 0) - quantity
        print(f"{termcolor.colored('Sold', 'red')} {termcolor.colored(symbol, 'magenta')} {quantity:.2f} shares @ ${price:.2f}")

        # Update daily shares for the current date
        current_date = self.start_date.strftime('%Y-%m-%d')
        if current_date not in self.daily_shares:
            self.daily_shares[current_date] = {}
        self.daily_shares[current_date][symbol] = self.shares[symbol]

    def get_annualized_return(self):
        years = max((self.inital_end_date - self.inital_start_date).days / 365, 1)  # Use minimum of 1 year
        total_return = self.get_value() / self.starting_capital - 1
        return (1 + total_return) ** (1 / years) - 1

    def backtest(self):
        current_date = self.start_date
        # Process initial investment immediately (using starting_capital only)
        self.next_month()  # Process initial investment immediately
        
        while current_date <= self.end_date:
            if current_date + relativedelta(months=1) > datetime.now():
                break
                
            # Monthly rebalancing
            if current_date.day == self.start_date.day and current_date > self.inital_start_date:  # Only add monthly investment after initial month
                self.cash += self.monthly_investment
                self.start_date = current_date
                self.next_month()
                self.start_date += relativedelta(months=1)
            else:
                last_date = current_date - relativedelta(days=1)
                if last_date.strftime('%Y-%m-%d') in self.daily_shares:
                    self.daily_shares[current_date.strftime('%Y-%m-%d')] = self.daily_shares[last_date.strftime('%Y-%m-%d')].copy()
            
            current_date += relativedelta(days=1)

        # Display holdings
        df = pd.DataFrame(list(self.shares.items()), columns=['Symbol', 'Shares'])
        print("\nFinal Holdings:")
        print(df)

        self.get_daily_values()
        
        # Calculate and display statistics
        stats = self.calculate_portfolio_stats()
        print("\nPortfolio Statistics:")
        print(stats.to_string())

        # calculate the number of months between inital_start_date and end_date
        months = (self.inital_end_date.year - self.inital_start_date.year) * 12 + (self.inital_end_date.month - self.inital_start_date.month)
        total_contributions = (self.monthly_investment * months) + self.starting_capital
        print(f"\nTotal Contributions: ${total_contributions:.2f}")

        print(f"\nEnding Portfolio Value: ${self.get_value():.2f}")
        
        return self.daily_values

    def get_daily_values(self):
        symbols = list(self.shares.keys())
        if len(symbols) == 0:
            return
            
        daily_values = load_daily_values(tuple(sorted(symbols)), self.inital_start_date, self.inital_end_date)
        
        # Create a DataFrame to store daily shares
        dates = pd.date_range(self.inital_start_date, self.inital_end_date)
        
        # Initialize the first day's shares
        prev_shares = {symbol: 0 for symbol in symbols}
        
        # Fill in daily shares for all dates
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            if date_str in self.daily_shares:
                # Update with new share counts
                prev_shares.update(self.daily_shares[date_str])
            
            # Calculate total value for this day
            total_value = self.cash
            
            # Find the closest date in daily_values
            date_val = date.date()
            closest_idx = daily_values.index.get_indexer([date_val], method='nearest')[0]
            closest_date = daily_values.index[closest_idx]
            
            total_value += sum(prev_shares[symbol] * float(daily_values.loc[closest_date, symbol]) 
                              for symbol in symbols)


            self.daily_values.loc[date_val] = {
                'portfolio_value': total_value,
                'cash': self.cash
            }
        
        print(self.daily_values)

    def next_month(self):
        print(f"Date: {self.start_date}")
        self.cash += self.monthly_investment
        transactions = run_trading_system(self.rules, self.start_date)
        print(f"Transactions: {transactions}")


        # get buy transactions
        for symbol, percentage in transactions['buy'].items():
            df = load_historical_data(symbol, self.start_date)
            closest_date = df.index.get_indexer([self.start_date], method='nearest')[0]
            price = df['adj_close'].iloc[closest_date]

            shares = (self.cash - self.min_cash) * percentage / price
            self.buy(symbol, price, shares)

        for symbol, percentage in transactions['sell'].items():
            if symbol in self.shares:
                df = load_historical_data(symbol, self.start_date)
                closest_date = df.index.get_indexer([self.start_date], method='nearest')[0]
                price = df['adj_close'].iloc[closest_date]
                shares = self.shares[symbol] * percentage
                self.sell(symbol, price, shares)
            
        print(f"Cash Remaining: ${self.cash:.2f}")
        print(f"--------------\n")
        

    def get_value(self):
        total_value = self.cash
        self.end_date += relativedelta(months=1)
        for symbol, shares in self.shares.items():
            df = load_historical_data(symbol, self.end_date)
            price = df['adj_close'].iloc[-1]
            total_value += shares * price
        return total_value
    
    def spy_stats(self):
        """Calculate SPY comparison statistics"""

        spy_data = load_daily_values(('SPY',), self.inital_start_date, self.inital_end_date)
        spy_data['SPY'] = spy_data['SPY'].astype(float)
            
        # Get first available date's price
        first_price = spy_data['SPY'].iloc[0]
        spy_shares = self.starting_capital / first_price  # Initial shares bought
        spy_portfolio_value = spy_shares * spy_data['SPY']
        
        # If there are monthly investments, add them
        if self.monthly_investment > 0:
            # Use 'ME' instead of 'M' and convert dates to Timestamp
                        # Use 'MS' (Month Start) instead of 'ME' (Month End)
            monthly_dates = pd.date_range(
                pd.Timestamp(self.inital_start_date), 
                pd.Timestamp(self.inital_end_date), 
                freq='MS'
            )
            
            print(monthly_dates)
            for target_date in monthly_dates:
                # Convert target_date to same type as index
                target_date = pd.Timestamp(target_date)
                
                # Find closest date
                loc = spy_data.index.get_indexer([target_date], method='nearest')[0]
                closest_date = spy_data.index[loc]
                
                additional_shares = self.monthly_investment / spy_data.loc[closest_date, 'SPY']
                spy_shares += additional_shares
                # Update all future values to reflect the new shares
                spy_portfolio_value[closest_date:] = spy_shares * spy_data['SPY'][closest_date:]
        

        # print(spy_portfolio_value)
        return {
            'spy_values': spy_portfolio_value,
            'spy_final_value': float(spy_portfolio_value.iloc[-1]),
        }

    def get_total_stats(self):
        """Get all portfolio statistics including SPY comparison"""
        # Get portfolio stats
        portfolio_stats = self.calculate_portfolio_stats()
        
        # Get SPY comparison stats
        spy_data = self.spy_stats()
        # Combine all stats
        total_stats = {
            'portfolio_stats': portfolio_stats.to_dict(),
            'spy_stats': spy_data,
            'daily_values': self.daily_values
        }
        
        return total_stats

    def plot(self):
        """Plot portfolio performance vs SPY"""
        stats = self.get_total_stats()
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        # Set the y-axis formatter to use comma separator and prevent scientific notation
        ax = plt.gca()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: '${:,.2f}'.format(x)))
        
        # print(self.daily_values)
        # print(stats['spy_stats']['spy_values'])

        self.daily_values['portfolio_value'].plot(label='Portfolio: ${:,.2f}'.format(self.get_value()))
        stats['spy_stats']['spy_values'].plot(label='SPY: ${:,.2f}'.format(stats["spy_stats"]["spy_final_value"]))
        
        plt.title('Portfolio Value Comparison')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    start = time.time()
    start_date = datetime(2024, 1, 1)
    # end_date = datetime(2022, 1, 1)
    end_date = datetime.now()

    starting_capital = 1000
    monthly_investment = 100

    rules = load_rules('rules.json')

    portfolio = Portfolio(starting_capital, monthly_investment, rules, end_date, start_date)
    portfolio.backtest()
    
    end = time.time()
    print(f"Time taken: {end - start}")
    portfolio.plot()
