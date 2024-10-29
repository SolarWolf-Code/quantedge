import fastapi
from fastapi.middleware.cors import CORSMiddleware
from backtesting import Portfolio
from datetime import datetime
import numpy as np
import math
import pandas as pd
import json
from database import get_db_connection
from fastapi import FastAPI, HTTPException

app = fastapi.FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.floating, float)):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, pd.Timestamp):
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)

def clean_data_for_json(df):
    """Clean DataFrame to make it JSON serializable"""
    records = []
    for index, row in df.iterrows():
        clean_row = {}
        for column, value in row.items():
            if isinstance(value, (np.floating, float)):
                if math.isnan(value) or math.isinf(value):
                    clean_row[column] = None
                else:
                    clean_row[column] = float(value)
            elif isinstance(value, np.integer):
                clean_row[column] = int(value)
            else:
                clean_row[column] = value
        clean_row['date'] = index.strftime('%Y-%m-%d')
        records.append(clean_row)
    return records

@app.post("/backtest")
def backtest(payload: dict):
    start_date = payload["start_date"]
    end_date = payload["end_date"]
    starting_capital = payload["starting_capital"]
    monthly_investment = payload["monthly_investment"]
    rules = payload
    
    # convert start and end date to datetime
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date = datetime.strptime(end_date, "%Y-%m-%d")

    portfolio = Portfolio(starting_capital, monthly_investment, rules, end_date, start_date)
    portfolio.backtest()
    
    # Get all stats including SPY comparison
    stats = portfolio.get_total_stats()
    
    try:
        # Clean and convert the data for JSON serialization
        clean_results = clean_data_for_json(stats['daily_values'])
        
        # Convert SPY values to a proper DataFrame with date index
        spy_df = pd.DataFrame(
            stats['spy_stats']['spy_values'],
            index=stats['daily_values'].index
        )
        clean_spy_values = clean_data_for_json(spy_df)
        
        response_data = {
            "daily_values": clean_results,
            "spy_values": clean_spy_values,
            "stats": {}
        }

        # Carefully clean and add each stat
        for key, value in stats["portfolio_stats"].items():
            if isinstance(value, (np.floating, float)):
                if math.isnan(value) or math.isinf(value):
                    response_data["stats"][key] = None
                else:
                    response_data["stats"][key] = float(value)
            elif isinstance(value, np.integer):
                response_data["stats"][key] = int(value)
            else:
                response_data["stats"][key] = str(value)

        # Test JSON serialization before sending
        test_json = json.dumps(response_data, cls=CustomJSONEncoder)
        
        return fastapi.Response(
            content=test_json,
            media_type="application/json"
        )
        
    except Exception as e:
        print(f"Error preparing response: {str(e)}")
        # Return a simplified error response
        return fastapi.Response(
            content=json.dumps({
                "error": "Error preparing response data",
                "details": str(e)
            }),
            media_type="application/json",
            status_code=500
        )

@app.post("/save_strategy")
async def save_strategy(strategy: dict):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Convert rules to JSON string
                rules_json = json.dumps(strategy['rules'])
                
                # Insert or update the strategy
                cur.execute("""
                    INSERT INTO strategies (name, rules, user_id, created_at, updated_at)
                    VALUES (%s, %s, %s, NOW(), NOW())
                    ON CONFLICT (name, user_id) 
                    DO UPDATE SET 
                        rules = EXCLUDED.rules,
                        updated_at = NOW()
                    RETURNING id
                """, (strategy['name'], rules_json, strategy['user_id']))
                
                strategy_id = cur.fetchone()[0]
                conn.commit()
                
                return {"success": True, "strategy_id": strategy_id}
    except Exception as e:
        print(f"Error saving strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_all_strategies")
async def get_all_strategies():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, rules, created_at, updated_at
                    FROM strategies
                    ORDER BY updated_at DESC
                """)
                strategies = cur.fetchall()
                
                # Format each strategy as a dictionary
                return [
                    {
                        "id": strategy[0],
                        "name": strategy[1],
                        "rules": json.loads(strategy[2]) if isinstance(strategy[2], str) else strategy[2],
                        "created_at": strategy[3].isoformat() if strategy[3] else None,
                        "updated_at": strategy[4].isoformat() if strategy[4] else None
                    }
                    for strategy in strategies
                ]
    except Exception as e:
        print(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_strategy")
async def get_strategy(strategy_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, rules, created_at, updated_at
                    FROM strategies
                    WHERE id = %s
                """, (strategy_id,))
                strategy = cur.fetchone()
                if not strategy:
                    raise HTTPException(status_code=404, detail="Strategy not found")
                
                # Format the response as a dictionary
                return {
                    "id": strategy[0],
                    "name": strategy[1],
                    "rules": json.loads(strategy[2]) if isinstance(strategy[2], str) else strategy[2],
                    "created_at": strategy[3].isoformat() if strategy[3] else None,
                    "updated_at": strategy[4].isoformat() if strategy[4] else None
                }
    except Exception as e:
        print(f"Error getting strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        