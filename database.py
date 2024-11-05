import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Create a connection pool
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

def save_price_data(symbol, df):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO symbols (symbol)
                VALUES (%s)
                ON CONFLICT (symbol) DO NOTHING
            """, (symbol,))
            
            for index, row in df.iterrows():
                cur.execute("""
                    INSERT INTO prices (symbol, date, open, high, low, close, adj_close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol, date) DO UPDATE
                    SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                        close = EXCLUDED.close, adj_close = EXCLUDED.adj_close, volume = EXCLUDED.volume
                """, (
                    symbol,
                    index.date(),
                    float(row['open'].iloc[0]),
                    float(row['high'].iloc[0]),
                    float(row['low'].iloc[0]),
                    float(row['close'].iloc[0]),
                    float(row['adj_close'].iloc[0]),
                    int(row['volume'].iloc[0])
                ))

            conn.commit()
