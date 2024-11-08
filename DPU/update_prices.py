import yfinance as yf
from datetime import datetime
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# disable yfinance warnings and errors
logging.getLogger("yfinance").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}


connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,  # Increased max connections
    **DB_PARAMS
)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)

def get_all_tickers():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT symbol FROM symbols
            """)
            data = cur.fetchall()
            tickers = [ticker[0] for ticker in data]
            return tickers


def update_all_prices(current_day_only=False):
    tickers = get_all_tickers()
    print(f"Updating data for {len(tickers)} symbols")
    
    tickers_string = ",".join(tickers)
    if current_day_only:
        current_date = datetime.now().strftime('%Y-%m-%d')
        print(f"Fetching data for current day: {current_date}")
        tickers_data = yf.download(tickers_string, start=current_date)
    else:
        print("Fetching data for all days")
        tickers_data = yf.download(tickers_string)

    # Prepare batch data
    batch_data = []
    
    for ticker in tickers:
        # Access multi-index DataFrame correctly by selecting all price types for this ticker
        ticker_data = tickers_data.xs(ticker, axis=1, level=1)
        ticker_data = ticker_data.dropna()

        # Process each date for this ticker
        for date, row in ticker_data.iterrows():
            batch_data.append({
                'symbol': ticker,
                'adj_close': float(row['Adj Close']),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
                'date': date.strftime('%Y-%m-%d')
            })

    # Batch insert/update
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Using execute_values for bulk insert
            from psycopg2.extras import execute_values
            
            query = """
                INSERT INTO prices (symbol, date, open, high, low, close, adj_close, volume)
                VALUES %s
                ON CONFLICT (symbol, date) 
                DO UPDATE SET
                    open = EXCLUDED.open,
                    high = EXCLUDED.high,
                    low = EXCLUDED.low,
                    close = EXCLUDED.close,
                    adj_close = EXCLUDED.adj_close,
                    volume = EXCLUDED.volume
            """
            
            # Convert batch_data to tuples for execute_values
            values = [(d['symbol'], d['date'], d['open'], d['high'], d['low'], 
                      d['close'], d['adj_close'], d['volume']) for d in batch_data]
            
            execute_values(cur, query, values)
            conn.commit()

    print(f"Updated history for {len(tickers)} symbols")

if __name__ == "__main__":
    # Run once immediately when starting
    logging.info("Running initial price update...")
    update_all_prices(current_day_only=False)
    
    scheduler = BlockingScheduler()
    scheduler.add_job(
        update_all_prices,
        'cron',
        args=[True],  # Pass current_day_only=True
        hour=18,  # 6 PM
        timezone=timezone('US/Eastern')
    )
    
    logging.info("Starting scheduler. Price updates will run daily at 6 PM EST.")
    scheduler.start()
