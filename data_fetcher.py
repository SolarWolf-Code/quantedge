from functools import lru_cache
import yfinance as yf
import pandas as pd
from database import get_db_connection, save_price_data


def check_symbol_exists(symbol):
    try:
        yf.Ticker(symbol).info
        return True
    except Exception as e:
        return False

def get_trading_days():
    # loads SPY and returns trading days
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date FROM prices WHERE symbol = 'SPY'
            """)
            trading_days = cur.fetchall()

    # put in list format
    trading_days = [day[0] for day in trading_days]
    return trading_days


@lru_cache(maxsize=128)
def get_earliest_date(symbol):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MIN(date) FROM prices WHERE symbol = %s
                """, (symbol,))
                earliest_date = cur.fetchone()[0]
                if earliest_date is None:
                    raise ValueError(f"No data found for symbol: {symbol}")
        except Exception as e:
            # check if symbol exists
            if not check_symbol_exists(symbol):
                raise ValueError(f"Symbol {symbol} does not exist")
            else:
                # fetch data from yahoo finance
                get_price_data_as_dataframe(symbol)
                earliest_date = get_earliest_date(symbol)

    return earliest_date

def get_price_data_as_dataframe(symbol):
    print(f"Fetching data for symbol: {symbol}...")
    df = yf.download(symbol, progress=False)
    if df.empty:
        raise ValueError(f"No data found for symbol: {symbol}")
    
    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}, inplace=True)

    save_price_data(symbol, df)

@lru_cache(maxsize=128)
def load_historical_data(symbol, end_date=None):
    # Convert end_date to string if it exists, since datetime objects aren't hashable
    cache_key_date = end_date.isoformat() if end_date else None
    return _load_historical_data(symbol, end_date)

def _load_historical_data(symbol, end_date=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if end_date:
                cur.execute("""
                    SELECT date, open, high, low, close, adj_close, volume
                    FROM prices
                    WHERE symbol = %s AND date <= %s
                    ORDER BY date
                """, (symbol, end_date))
            else:
                cur.execute("""
                    SELECT date, open, high, low, close, adj_close, volume
                    FROM prices
                    WHERE symbol = %s
                    ORDER BY date
                """, (symbol,))
            data = cur.fetchall()

    if not data:
        get_price_data_as_dataframe(symbol)
        df = load_historical_data(symbol, end_date)
        if end_date:
            df = df[(df.index.date <= end_date.date())]

    else:
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)
        numeric_columns = ['open', 'high', 'low', 'close', 'adj_close']
        df[numeric_columns] = df[numeric_columns].astype(float)
        df['volume'] = df['volume'].astype(int)
    
    return df

@lru_cache(maxsize=128)
def load_daily_values(symbols, date):
    # Convert dates to strings and symbols tuple to make it hashable
    cache_key_symbols = tuple(sorted(symbols))  # Sort to ensure consistent caching
    cache_key_date = date.isoformat()
    return _load_daily_values(cache_key_symbols, cache_key_date)

def _load_daily_values(symbols, date):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date, symbol, adj_close
                FROM prices
                WHERE symbol IN %s AND date = %s
                        
            """, (tuple(symbols), date))
            data = cur.fetchall()

    df = pd.DataFrame(data, columns=['date', 'symbol', 'adj_close'])
    # Pivot the DataFrame to have symbols as columns
    df_pivoted = df.pivot(index='date', columns='symbol', values='adj_close')
    return df_pivoted


if __name__ == "__main__":
    print(check_symbol_exists("asdasd"))
