from functools import lru_cache
import yfinance as yf
import pandas as pd
from database import get_db_connection, save_price_data


@lru_cache(maxsize=128)
def get_earliest_date(symbol):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # First check if symbol exists in symbols table
            cur.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM symbols WHERE symbol = %s
                ) as symbol_exists,
                EXISTS (
                    SELECT 1 FROM prices WHERE symbol = %s
                ) as prices_exist
            """, (symbol, symbol))
            result = cur.fetchone()
            symbol_exists, prices_exist = result
            
            if symbol_exists and not prices_exist:
                # Symbol exists but no price data - fetch it
                print(f"Symbol {symbol} exists but has no price data. Fetching...")
                get_price_data_as_dataframe(symbol)
            
            # Now get the earliest date
            cur.execute("""
                SELECT MIN(date) FROM prices WHERE symbol = %s
            """, (symbol,))
            earliest_date = cur.fetchone()[0]
            
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
def load_daily_values(symbols, start_date, end_date):
    # Convert dates to strings and symbols tuple to make it hashable
    cache_key_symbols = tuple(sorted(symbols))  # Sort to ensure consistent caching
    cache_key_start = start_date.isoformat()
    cache_key_end = end_date.isoformat()
    return _load_daily_values(cache_key_symbols, start_date, end_date)

def _load_daily_values(symbols, start_date, end_date):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Now get all the price data
            cur.execute("""
                SELECT date, symbol, adj_close
                FROM prices
                WHERE symbol IN %s AND date >= %s AND date <= %s
            """, (tuple(symbols), start_date, end_date))
            data = cur.fetchall()

    df = pd.DataFrame(data, columns=['date', 'symbol', 'adj_close'])
    # Pivot the DataFrame to have symbols as columns
    df_pivoted = df.pivot(index='date', columns='symbol', values='adj_close')
    return df_pivoted
