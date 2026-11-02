from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3
from datetime import datetime
import pytz

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
        
        us_tz = pytz.timezone('America/New_York')
        result = []
        
        for row in rows:
            row_dict = dict(row)
            commence_time = row_dict.get("commence_time")
            
            # Chuẩn hóa ngày giờ theo chuẩn Mỹ (America/New_York) ngay từ backend
            if commence_time:
                try:
                    # Xử lý chuỗi ISO time
                    clean_time = commence_time.replace('Z', '+00:00')
                    dt = datetime.fromisoformat(clean_time)
                    if dt.tzinfo is None:
                        dt = pytz.utc.localize(dt)
                    
                    # Chuyển đổi sang múi giờ miền Đông nước Mỹ (ET)
                    dt_us = dt.astimezone(us_tz)
                    
                    # Gán thêm trường ngày chuẩn theo giờ Mỹ (YYYY-MM-DD) để phía frontend lọc chính xác
                    row_dict["us_date"] = dt_us.strftime('%Y-%m-%d')
                except Exception:
                    row_dict["us_date"] = str(commence_time)[:10]
            else:
                row_dict["us_date"] = ""
                
            result.append(row_dict)
            
        return result
    except Exception as e:
        return {"error": str(e)}