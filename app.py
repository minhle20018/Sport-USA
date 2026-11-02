from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
from datetime import datetime, timezone, timedelta

app = FastAPI(title="VMAH US Sports AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found"}

@app.get("/api/daily-picks")
def get_daily_picks():
    try:
        db_path = "sports_bettor.db"
        if not os.path.exists(db_path):
            return []
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            conn.close()
            return []
        
        table_name = tables[0][0]
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        conn.close()
        
        us_offset = timedelta(hours=-5)
        us_tz = timezone(us_offset)
        
        result = []
        for row in rows:
            row_dict = dict(row)
            commence_time = str(row_dict.get("commence_time", ""))
            
            try:
                clean_time = commence_time.replace('Z', '+00:00')
                dt = datetime.fromisoformat(clean_time)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                dt_us = dt.astimezone(us_tz)
                row_dict["us_date"] = dt_us.strftime('%Y-%m-%d')
            except Exception:
                row_dict["us_date"] = commence_time[:10] if len(commence_time) >= 10 else ""
            
            # --- LOGIC TỰ ĐỘNG ĐỐI CHIẾU KẾT QUẢ WIN / LOSE ---
            status = row_dict.get("status", "Scheduled")
            home_score = row_dict.get("home_score")
            away_score = row_dict.get("away_score")
            
            if status == "Finished" and home_score is not None and away_score is not None:
                is_home_better = row_dict.get("ai_home_prob", 0) >= row_dict.get("ai_away_prob", 0)
                predicted_winner = row_dict.get("home_team") if is_home_better else row_dict.get("away_team")
                actual_winner = row_dict.get("home_team") if home_score > away_score else row_dict.get("away_team")
                
                if predicted_winner == actual_winner:
                    row_dict["result_status"] = "WIN"
                else:
                    row_dict["result_status"] = "LOSE"
            else:
                row_dict["result_status"] = "PENDING"
                
            result.append(row_dict)
            
        return result
    except Exception as e:
        return {"error": str(e)}