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


    def get_annualized_return(self):
        years = max((self.inital_end_date - self.inital_start_date).days / 365, 1)  # Use minimum of 1 year
        total_return = self.get_value() / self.starting_capital - 1
        return (1 + total_return) ** (1 / years) - 1

    def backtest(self):
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date + relativedelta(months=1) > datetime.now():
                break
                
            # Monthly rebalancing
            if current_date.day == self.start_date.day:  # Only rebalance on same day of month
                self.cash += self.monthly_investment
                self.start_date = current_date
                if current_date != self.inital_start_date:
                    self.start_date += relativedelta(months=1)
                self.next_month()
            
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

        print(f"\nEnding Portfolio Value: ${self.get_value():.2f}")
        
        return self.daily_values

    def get_daily_values(self):
        symbols = list(self.shares.keys())
        daily_values = load_daily_values(tuple(sorted(symbols)), self.inital_start_date, self.inital_end_date)

        for index, row in daily_values.iterrows():
            total_value = self.cash  # Start with cash
            for symbol in self.shares:
                total_value += self.shares[symbol] * float(row[symbol])
            
            self.daily_values.loc[index] = {
                'portfolio_value': total_value,
                'cash': self.cash
            }

    def next_month(self):
        print(f"Date: {self.start_date}")
        self.cash += self.monthly_investment
        purchases = run_trading_system(self.rules, self.start_date)
        # print(f"\nAvailable cash: ${self.cash:.2f}")
        
        for symbol, percentage in purchases.items():
            df = load_historical_data(symbol, self.start_date)
            price = df['close'].iloc[-1]
            available_cash = self.cash
            if available_cash < 0:
                continue  # Skip if we don't have enough cash
                
            shares = (available_cash - self.min_cash) * percentage / price

            if shares * price > 5:
                shares = round(shares, 3)
                
            if shares > 0:  # Only buy if we have at least some shares
                self.buy(symbol, price, shares)
        
        print(f"Cash Remaining: ${self.cash:.2f}")
        print(f"--------------\n")
        

    def get_value(self):
        total_value = self.cash
        self.end_date += relativedelta(months=1)
        for symbol, shares in self.shares.items():
            df = load_historical_data(symbol, self.end_date)
            price = df['close'].iloc[-1]
            total_value += shares * price
        return total_value
    
    def spy_stats(self):
        """Calculate SPY comparison statistics"""
        spy_data = load_daily_values(('SPY',), self.inital_start_date, self.inital_end_date)
        spy_data['SPY'] = spy_data['SPY'].astype(float)
        
        # Calculate SPY portfolio value (if we had invested everything in SPY)
        spy_shares = self.starting_capital / spy_data['SPY'].iloc[0]  # Initial shares bought
        spy_portfolio_value = spy_shares * spy_data['SPY']
        
        # If there are monthly investments, add them
        if self.monthly_investment > 0:
            # Calculate monthly dates between start and end
            monthly_dates = pd.date_range(self.inital_start_date, self.inital_end_date, freq='M')
            for date in monthly_dates:
                if date in spy_data.index:
                    additional_shares = self.monthly_investment / spy_data.loc[date, 'SPY']
                    spy_shares += additional_shares
                    # Update all future values to reflect the new shares
                    spy_portfolio_value[date:] = spy_shares * spy_data['SPY'][date:]
        
        return {
            'spy_values': spy_portfolio_value,
            'spy_final_value': float(spy_portfolio_value.iloc[-1]),
            'spy_initial_value': float(spy_portfolio_value.iloc[0])
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
        self.daily_values['portfolio_value'].plot(label=f'Portfolio: ${stats["spy_stats"]["spy_final_value"]:,.2f}')
        stats['spy_stats']['spy_values'].plot(label=f'SPY: ${stats["spy_stats"]["spy_final_value"]:,.2f}')
        
        plt.title('Portfolio Value Comparison')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    start = time.time()
    start_date = datetime(2019, 1, 1)
    # end_date = datetime(2022, 1, 1)
    end_date = datetime.now()

    starting_capital = 10000
    monthly_investment = 0

    rules = load_rules('rules.json')

    portfolio = Portfolio(starting_capital, monthly_investment, rules, end_date, start_date)
    portfolio.backtest()
    
    end = time.time()
    print(f"Time taken: {end - start}")
    portfolio.plot()
