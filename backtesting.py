from datetime import datetime
from trading_system import load_rules, run_trading_system
from data_fetcher import load_historical_data, get_trading_days, load_daily_values
import termcolor
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class Share:
    shares: float
    price: float

class Portfolio:
    def __init__(self, starting_capital, monthly_investment, rules, end_date, start_date):
        self.starting_capital = starting_capital
        self.monthly_investment = monthly_investment
        self.cash = starting_capital
        self.shares = {} # symbol: Share
        self.rules = rules
        self.end_date = end_date
        self.start_date = start_date
        self.min_cash = 5
        self.inital_start_date = start_date
        self.inital_end_date = end_date
        self.portfolio_value_history = {}

        # self.spy_shares_history = {}
        self.spy_value_history = {}
        self.spy_shares = 0
        self.spy_cash = starting_capital



    def buy(self, symbol, price, quantity, date):
        cost = price * quantity
        self.cash -= cost
        if symbol not in self.shares:
            self.shares[symbol] = Share(quantity, price)
        else:
            self.shares[symbol].shares += quantity
            self.shares[symbol].price = (self.shares[symbol].price * self.shares[symbol].shares + price * quantity) / (self.shares[symbol].shares + quantity)
        print(f"{termcolor.colored('Bought', 'green')} {termcolor.colored(symbol, 'magenta')} {quantity:.2f} shares @ ${price:.2f}")

    def sell(self, symbol, price, quantity, date):
        self.cash += price * quantity
        if self.shares[symbol].shares == quantity:
            del self.shares[symbol]
        else:
            self.shares[symbol].shares -= quantity
        print(f"{termcolor.colored('Sold', 'red')} {termcolor.colored(symbol, 'magenta')} {quantity:.2f} shares @ ${price:.2f}")


    def is_last_trading_day_of_month(self, date, trading_days, first_of_month=True):
        """
        Check if the date is the first or last trading day of that month
        """
        if date.date() in trading_days:
            if first_of_month:
                last_trading_day = [day for day in trading_days if day.month == date.month and day.year == date.year][0]
            else:
                last_trading_day = [day for day in trading_days if day.month == date.month and day.year == date.year][-1]
            return date.date() == last_trading_day
        return False

    def current_holdings(self):
        df = pd.DataFrame(list(self.shares.items()), columns=['Symbol', 'Shares'])
        return df

    def stats(self):
        """Calculate various portfolio performance metrics"""
        df = pd.DataFrame(list(self.portfolio_value_history.items()), columns=['Date', 'Portfolio Value'])
        # Convert Date column to datetime and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        
        # same for spy
        spy_df = pd.DataFrame(list(self.spy_value_history.items()), columns=['Date', 'SPY Value'])
        spy_df['Date'] = pd.to_datetime(spy_df['Date'])
        spy_df = spy_df.set_index('Date')

        # Risk-free rate (using 2% annual as example)
        risk_free_rate = 0.02
        daily_rf_rate = (1 + risk_free_rate) ** (1/252) - 1
        
        # Calculate metrics
        stats = {
            'Total Return': self.calculate_total_return(df) * 100,
            'CAGR': self.calculate_cagr(df) * 100,
            'Max Drawdown': self.calculate_max_drawdown(df) * 100,
            'Volatility': self.calculate_volatility(df) * 100,
            'Calmar Ratio': self.calculate_calmar_ratio(df),
            'Sharpe Ratio': self.calculate_sharpe_ratio(df, daily_rf_rate),
            'Sortino Ratio': self.calculate_sortino_ratio(df, daily_rf_rate),
            # 'Ulcer Index': self.calculate_ulcer_index(df),
            # 'Martin Ratio': self.calculate_martin_ratio(df, daily_rf_rate),
            'Beta': self.calculate_beta(df, spy_df),
        }
        return stats

    def calculate_beta(self, df, spy_df):
        return df['Portfolio Value'].pct_change().corr(spy_df['SPY Value'].pct_change())

    def calculate_martin_ratio(self, df, daily_rf_rate):
        return (self.calculate_cagr(df) - daily_rf_rate) / self.calculate_ulcer_index(df)

    def calculate_ulcer_index(self, df):
        """Calculate Ulcer Index"""
        portfolio_values = df['Portfolio Value']
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values / rolling_max - 1) * 100
        return np.sqrt(np.mean(drawdowns**2))

    def calculate_downside_deviation(self, df, daily_rf_rate):
        return df['Portfolio Value'].pct_change().sub(daily_rf_rate).clip(lower=0).std() * np.sqrt(252)

    def calculate_sortino_ratio(self, df, daily_rf_rate):
        return (self.calculate_cagr(df) - daily_rf_rate) / self.calculate_downside_deviation(df, daily_rf_rate)

    def calculate_sharpe_ratio(self, df, daily_rf_rate):
        return (self.calculate_cagr(df) - daily_rf_rate) / self.calculate_volatility(df)

    def calculate_calmar_ratio(self, df):
        return self.calculate_cagr(df) / self.calculate_max_drawdown(df)

    def calculate_volatility(self, df):
        return df['Portfolio Value'].pct_change().std() * np.sqrt(252)

    def calculate_max_drawdown(self, df):
        return df['Portfolio Value'].div(df['Portfolio Value'].cummax()).sub(1).min()

    def calculate_cagr(self, df):
        return (df['Portfolio Value'].iloc[-1] / df['Portfolio Value'].iloc[0]) ** (252 / (df.index[-1] - df.index[0]).days) - 1

    def calculate_total_return(self, df):
        return df['Portfolio Value'].iloc[-1] / df['Portfolio Value'].iloc[0] - 1

    def backtest(self):
        current_date = self.start_date
        # get valid trading days
        trading_days = get_trading_days()
        # print(trading_days)

        while current_date <= self.end_date:
            if current_date + relativedelta(months=1) > datetime.now(): # stop if the next month is in the future. this might not be correct
                break
            
            if self.is_last_trading_day_of_month(current_date, trading_days):
                self.spy_buy_and_hold(current_date)
                self.next_month(current_date)

            current_date += relativedelta(days=1)
        
        self.get_daily_values()

        print(self.stats())


    def spy_buy_and_hold(self, date):
        self.spy_cash += self.monthly_investment
        # buy spy
        df = load_historical_data('SPY', date)
        closest_date = df.index.get_indexer([date], method='nearest')[0]
        price = df['adj_close'].iloc[closest_date]
        shares = (self.spy_cash - self.min_cash) / price
        # self.spy_shares_history[date.strftime('%Y-%m-%d')] = shares
        self.spy_shares += shares

        # subtract cash from spy
        self.spy_cash -= price * shares

    def next_month(self, date):
        print(f"Running for {date}")
        self.cash += self.monthly_investment
        transactions = run_trading_system(self.rules, date)


        # get buy transactions
        for symbol, percentage in transactions['buy'].items():
            df = load_historical_data(symbol, date)
            closest_date = df.index.get_indexer([date], method='nearest')[0]
            price = df['adj_close'].iloc[closest_date]
            shares = (self.cash - self.min_cash) * percentage / price
            self.buy(symbol, price, shares, date)

        for symbol, percentage in transactions['sell'].items():
            if symbol in self.shares:
                df = load_historical_data(symbol, date)
                closest_date = df.index.get_indexer([date], method='nearest')[0]
                price = df['adj_close'].iloc[closest_date]
                shares = self.shares[symbol] * percentage
                self.sell(symbol, price, shares, date)
        
        # update current shres
            
        print(f"Cash Remaining: ${self.cash:.2f}")
        print(f"--------------\n")

    def get_daily_values(self): # TODO: fix this. the shares are only being account for at the end of the backtest.
        symbols = list(self.shares.keys())
        if len(symbols) == 0:
            return
        daily_values = load_daily_values(tuple(sorted(symbols)), self.inital_start_date, self.inital_end_date)

        for index, row in daily_values.iterrows():
            # total_value = self.cash  # Start with cash
            total_value = 0
            for symbol in self.shares:
                total_value += self.shares[symbol].shares * float(row[symbol])
            
            self.portfolio_value_history[index] = total_value
        
        # spy
        spy_daily_values = load_daily_values(('SPY',), self.inital_start_date, self.inital_end_date)
        self.spy_value_history[self.inital_start_date.strftime('%Y-%m-%d')] = self.spy_cash
        for index, row in spy_daily_values.iterrows():
            self.spy_value_history[index] = self.spy_cash + self.spy_shares * float(row['SPY'])

    # def get_total_stats(self):
    #     """Get all portfolio statistics including SPY comparison"""
    #     # Get portfolio stats
    #     portfolio_stats = self.calculate_portfolio_stats()
        
    #     # Get SPY comparison stats
    #     spy_data = self.spy_stats()
    #     # Combine all stats
    #     total_stats = {
    #         'portfolio_stats': portfolio_stats.to_dict(),
    #         'spy_stats': spy_data,
    #         'daily_values': self.daily_values
    #     }
        
    #     return total_stats

    def plot(self):
        """Plot portfolio performance vs SPY"""
        # stats = self.get_total_stats()
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        # Set the y-axis formatter to use comma separator and prevent scientific notation
        ax = plt.gca()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: '${:,.2f}'.format(x)))
        
        # print(self.daily_values)
        # print(stats['spy_stats']['spy_values'])

        # conver to dataframe
        portfolio_df = pd.DataFrame(self.portfolio_value_history.items(), columns=['Date', 'Portfolio Value'])
        spy_df = pd.DataFrame(self.spy_value_history.items(), columns=['Date', 'SPY Value'])

        portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
        spy_df['Date'] = pd.to_datetime(spy_df['Date'])

        portfolio_df = portfolio_df.set_index('Date')
        spy_df = spy_df.set_index('Date')

        # remove first row from spy
        spy_df = spy_df.iloc[1:]

        # print first rows of both
        print(portfolio_df.head())
        print(spy_df.head())

        portfolio_df['Portfolio Value'].plot(label='Portfolio: ${:,.2f}'.format(portfolio_df['Portfolio Value'].iloc[-1]))
        spy_df['SPY Value'].plot(label='SPY: ${:,.2f}'.format(spy_df['SPY Value'].iloc[-1]))
        
        plt.title('Portfolio Value Comparison')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value ($)')
        plt.legend()
        plt.grid(True)
        plt.show()

if __name__ == "__main__":
    start = time.time()
    start_date = datetime(2020, 1, 1)
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
