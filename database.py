import os
import psycopg2
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

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

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
