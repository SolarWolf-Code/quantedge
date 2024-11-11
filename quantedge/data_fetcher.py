from functools import lru_cache
import yfinance as yf
import pandas as pd
from quantedge.database import get_db_connection, save_price_data


def check_symbol_exists(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # Try to access info - this will fail for invalid symbols
        info = ticker.info
        return info.get("symbol", None) is not None
    except Exception as e:
        # Check if it's a 404 error or any other error
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
        except Exception:
            # check if symbol exists
            if not check_symbol_exists(symbol):
                # raise ValueError(f"Symbol {symbol} does not exist")
                return None
            else:
                # fetch data from yahoo finance
                get_price_data_as_dataframe(symbol)
                earliest_date = get_earliest_date(symbol)

    return earliest_date

def get_price_data_as_dataframe(symbol):
    # print(f"Fetching data for symbol: {symbol}...")
    try:
        df = yf.download(symbol, progress=False)
        if df.empty:
            return None
        
        df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}, inplace=True)

        save_price_data(symbol, df)
    except Exception:
        return None
    
    return df


@lru_cache(maxsize=128)
def load_historical_data(symbol, end_date=None):
    # Convert end_date to string if it exists, since datetime objects aren't hashable
    cache_key_date = end_date if end_date else None
    return _load_historical_data(symbol, cache_key_date)

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
        df = get_price_data_as_dataframe(symbol)
        if not df:
            return None
        else:
            if end_date:
                df = df[(df.index.date <= end_date.date())]
    else:
        # only keep adj_close column and rename it to close
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])
        df.drop(columns=['close'], inplace=True)
        df.rename(columns={'adj_close': 'close'}, inplace=True)
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)
    
    return df

@lru_cache(maxsize=128)
def load_daily_values(symbols, start_date, end_date):
    # Convert dates to strings and symbols tuple to make it hashable
    cache_key_symbols = tuple(sorted(symbols))  # Sort to ensure consistent caching
    cache_key_start_date = start_date
    cache_key_end_date = end_date
    return _load_daily_values(cache_key_symbols, cache_key_start_date, cache_key_end_date)

def _load_daily_values(symbols, start_date, end_date):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT date, symbol, adj_close
                FROM prices
                WHERE symbol IN %s AND date BETWEEN %s AND %s
                        
            """, (tuple(symbols), start_date, end_date))
            data = cur.fetchall()

    if not data:
        return None

    df = pd.DataFrame(data, columns=['date', 'symbol', 'close'])
    # Convert date column to datetime.date
    df['date'] = pd.to_datetime(df['date']).dt.date
    # Pivot the DataFrame to have symbols as columns
    df_pivoted = df.pivot(index='date', columns='symbol', values='close')
    return df_pivoted