import yfinance as yf
import pandas as pd
from database import get_db_connection, save_price_data

def get_price_data_as_dataframe(symbol):
    print(f"Fetching data for symbol: {symbol}...")
    df = yf.download(symbol, progress=False)
    if df.empty:
        raise ValueError(f"No data found for symbol: {symbol}")
    
    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"}, inplace=True)

    save_price_data(symbol, df)

def load_historical_data(symbol, start_date=None, end_date=None):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if start_date and end_date:
                cur.execute("""
                    SELECT date, open, high, low, close, adj_close, volume
                    FROM prices
                    WHERE symbol = %s AND date BETWEEN %s AND %s
                    ORDER BY date
                """, (symbol, start_date, end_date))
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
        df = load_historical_data(symbol, start_date, end_date)
        if start_date and end_date:
            df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]

    else:
        df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'adj_close', 'volume'])
        df.set_index('date', inplace=True)
        df.index = pd.to_datetime(df.index)
        numeric_columns = ['open', 'high', 'low', 'close', 'adj_close']
        df[numeric_columns] = df[numeric_columns].astype(float)
        df['volume'] = df['volume'].astype(int)
    
    return df
