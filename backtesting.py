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
import decimal

@dataclass
class Share:
    shares: decimal.Decimal
    price: decimal.Decimal

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
        self.portfolio_shares_history = {}
        self.portfolio_cash_history = {}

        self.spy_value_history = {}
        self.spy_shares_history = {}
        self.spy_shares = 0
        self.spy_cash = starting_capital
        self.spy_cash_history = {}

        # Add new instance variable
        self.monthly_trading_days = self._precompute_monthly_trading_days(get_trading_days())

    def _precompute_monthly_trading_days(self, trading_days):
        """Precompute first and last trading days for each month"""
        monthly_days = {}
        for day in trading_days:
            key = (day.year, day.month)
            if key not in monthly_days:
                monthly_days[key] = {'first': day, 'last': day}
            else:
                monthly_days[key]['last'] = day
        return monthly_days

    def buy(self, symbol, price, quantity, date, previous_shares):
        cost = price * quantity
        self.cash -= cost
        if symbol not in self.shares:
            self.shares[symbol] = Share(quantity, price)
        else:
            self.shares[symbol].shares += quantity
            self.shares[symbol].price = (self.shares[symbol].price * self.shares[symbol].shares + price * quantity) / (self.shares[symbol].shares + quantity)


        # update portfolio shares history using previous shares
        existing_shares = previous_shares.get(symbol, 0)
        if date.date() not in self.portfolio_shares_history:
            self.portfolio_shares_history[date.date()] = previous_shares
        self.portfolio_shares_history[date.date()][symbol] = existing_shares + quantity
        # print(self.portfolio_shares_history)
        # print("-----")

        print(f"{termcolor.colored('Bought', 'green')} {termcolor.colored(symbol, 'magenta')} {quantity:.2f} shares @ ${price:.2f}")

    def sell(self, symbol, price, quantity, date, previous_shares):
        self.cash += price * quantity
        if self.shares[symbol].shares == quantity:
            del self.shares[symbol]
        else:
            self.shares[symbol].shares -= quantity
            
        existing_shares = previous_shares.get(symbol, 0)
        if date.date() not in self.portfolio_shares_history:
            self.portfolio_shares_history[date.date()] = previous_shares
        self.portfolio_shares_history[date.date()][symbol] = existing_shares - quantity

        print(f"{termcolor.colored('Sold', 'red')} {termcolor.colored(symbol, 'magenta')} {quantity:.2f} shares @ ${price:.2f}")


    def is_last_trading_day_of_month(self, date, trading_days, first_of_month=True):
        """
        Check if the date is the first or last trading day of that month
        """
        if date.date() in trading_days:
            key = (date.year, date.month)
            if key in self.monthly_trading_days:
                target_day = self.monthly_trading_days[key]['first' if first_of_month else 'last']
                return date.date() == target_day
        return False

    def current_holdings(self):
        df = pd.DataFrame([(symbol, share.shares) for symbol, share in self.shares.items()], columns=['Symbol', 'Shares'])
        return df

    def stats(self, value_history=None):
        """Calculate various portfolio performance metrics"""

        if value_history is None:
            value_history = self.portfolio_value_history
        df = pd.DataFrame(list(value_history.items()), columns=['Date', 'Portfolio Value'])
        # Convert Date column to datetime and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        # convert to decimal.Decimal
        df['Portfolio Value'] = df['Portfolio Value'].astype(float)
        df = df.set_index('Date')
        
        # same for spy
        spy_df = pd.DataFrame(list(self.spy_value_history.items()), columns=['Date', 'SPY Value'])
        spy_df['Date'] = pd.to_datetime(spy_df['Date'])
        spy_df['SPY Value'] = spy_df['SPY Value'].astype(float)
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

        # conver to dataframe
        stats_df = pd.DataFrame(stats, index=[0])
        return stats_df
    
    def spy_stats(self):
        """Calculate various SPY performance metrics"""
        return self.stats(self.spy_value_history)

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

        while current_date <= self.end_date:
            if current_date + relativedelta(months=1) > datetime.now(): # stop if the next month is in the future. this might not be correct
                break
            
            if current_date.date() in trading_days:
                if self.is_last_trading_day_of_month(current_date, trading_days):
                    self.spy_buy_and_hold(current_date)
                    self.next_month(current_date)
                else:
                    if len(self.spy_shares_history) > 0:
                        previous_day = sorted(self.spy_shares_history.keys())[-1]
                        self.spy_shares_history[current_date.date()] = self.spy_shares_history[previous_day]
                        self.portfolio_shares_history[current_date.date()] = self.portfolio_shares_history.get(previous_day, {})
                        self.spy_cash_history[current_date.date()] = self.spy_cash_history[previous_day]
                        self.portfolio_cash_history[current_date.date()] = self.portfolio_cash_history[previous_day]
                    else:
                        self.spy_shares_history[current_date.date()] = 0
                        self.portfolio_shares_history[current_date.date()] = {}
                        self.spy_cash_history[current_date.date()] = self.spy_cash
                        self.portfolio_cash_history[current_date.date()] = self.cash
                        
            current_date += relativedelta(days=1)
        
        self.get_daily_values()


    def spy_buy_and_hold(self, date):
        self.spy_cash += self.monthly_investment
        # buy spy
        df = load_historical_data('SPY', date)
        closest_date = df.index.get_indexer([date], method='nearest')[0]
        price = df['adj_close'].iloc[closest_date]
        shares = (self.spy_cash - self.min_cash) / price
        self.spy_shares += shares
        
        # Carry forward previous shares and add new shares
        previous_shares = 0
        if len(self.spy_shares_history) > 0:
            previous_date = sorted(self.spy_shares_history.keys())[-1]
            previous_shares = self.spy_shares_history[previous_date]
        self.spy_shares_history[date.date()] = previous_shares + shares

        # subtract cash from spy
        self.spy_cash -= price * shares
        self.spy_cash_history[date.date()] = self.spy_cash

    def next_month(self, date):
        print(f"Running for {date}")
        self.cash += self.monthly_investment
        transactions = run_trading_system(self.rules, date)


        if len(self.portfolio_shares_history) > 0:
            previous_date = sorted(self.portfolio_shares_history.keys())[-1]
            previous_shares = self.portfolio_shares_history[previous_date].copy()
        else:
            previous_shares = {}

        for symbol, percentage in transactions['sell'].items():
            if symbol in self.shares:
                df = load_historical_data(symbol, date)
                closest_date = df.index.get_indexer([date], method='nearest')[0]
                price = df['adj_close'].iloc[closest_date]
                # convert percentage to decimal.Decimal
                percentage = decimal.Decimal(percentage)
                shares = self.shares[symbol].shares * percentage
                self.sell(symbol, price, shares, date, previous_shares)

        for symbol, percentage in transactions['buy'].items():
            df = load_historical_data(symbol, date)
            closest_date = df.index.get_indexer([date], method='nearest')[0]
            price = df['adj_close'].iloc[closest_date]
            # convert percentage to decimal.Decimal
            percentage = decimal.Decimal(percentage)
            shares = (self.cash - self.min_cash) * percentage / price
            self.buy(symbol, price, shares, date, previous_shares)

        
        self.portfolio_cash_history[date.date()] = self.cash
        print(f"Cash Remaining: ${self.cash:.2f}")
        print(f"--------------\n")

    def get_daily_values(self): # TODO: fix this. the shares are only being account for at the end of the backtest.
        # need to get all symbols in portfolio_shares_history
        symbols = set([symbol for date in self.portfolio_shares_history for symbol in self.portfolio_shares_history[date]])
        symbols.add('SPY')
        if len(symbols) == 0:
            return
        daily_values = load_daily_values(tuple(sorted(symbols)), self.inital_start_date, self.inital_end_date)

        for date in self.portfolio_shares_history:
            total_value = 0
            # print(f"[{date}] PORTFOLIO SHARES: {self.portfolio_shares_history[date]}")
            for symbol in self.portfolio_shares_history[date]:
                total_value += decimal.Decimal(self.portfolio_shares_history[date][symbol]) * decimal.Decimal(daily_values.loc[date][symbol])
            self.portfolio_value_history[date] = total_value + decimal.Decimal(self.portfolio_cash_history[date])

        spy_daily_values = daily_values.loc[:, 'SPY']
        for date in self.spy_shares_history:
            price = spy_daily_values.loc[date]
            shares = self.spy_shares_history[date]
            self.spy_value_history[date] = shares * decimal.Decimal(price) + decimal.Decimal(self.spy_cash_history[date])


    def plot(self):
        """Plot portfolio performance vs SPY"""
        # Create the plot
        plt.figure(figsize=(12, 6))
        
        # Set the y-axis formatter to use comma separator and prevent scientific notation
        ax = plt.gca()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: '${:,.2f}'.format(x)))

        # conver to dataframe
        portfolio_df = pd.DataFrame(self.portfolio_value_history.items(), columns=['Date', 'Portfolio Value'])
        spy_df = pd.DataFrame(self.spy_value_history.items(), columns=['Date', 'SPY Value'])

        portfolio_df['Date'] = pd.to_datetime(portfolio_df['Date'])
        portfolio_df['Portfolio Value'] = portfolio_df['Portfolio Value'].astype(float)
        spy_df['Date'] = pd.to_datetime(spy_df['Date'])
        spy_df['SPY Value'] = spy_df['SPY Value'].astype(float)

        portfolio_df = portfolio_df.set_index('Date')
        spy_df = spy_df.set_index('Date')


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
    start_date = datetime(2012, 1, 1)
    end_date = datetime.now()

    starting_capital = 1000
    monthly_investment = 100

    rules = load_rules('rules.json')

    portfolio = Portfolio(starting_capital, monthly_investment, rules, end_date, start_date)
    portfolio.backtest()
    
    end = time.time()
    print(f"Time taken: {end - start}")
    print("Portfolio Stats:")
    print(portfolio.stats())
    print("SPY Stats:")
    print(portfolio.spy_stats())
    print("Current Holdings:")
    print(portfolio.current_holdings())
    portfolio.plot()
    # for date in portfolio.portfolio_shares_history:
    #     print(f"[{date}] {portfolio.portfolio_shares_history[date]}")


