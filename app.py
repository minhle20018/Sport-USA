from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sqlite3

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
        
        result = []
        for row in rows:
            row_dict = dict(row)
            commence_time = str(row_dict.get("commence_time", ""))
            
            # Lấy thẳng 10 ký tự đầu tiên của chuỗi thời gian (YYYY-MM-DD) làm us_date chuẩn gốc
            if len(commence_time) >= 10:
                row_dict["us_date"] = commence_time[:10]
            else:
                row_dict["us_date"] = ""
                
            result.append(row_dict)
            
        return result
    except Exception as e:
        return {"error": str(e)}