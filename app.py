from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json

app = FastAPI(title="VMAH US Sports AI Backend")

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trả về giao diện index.html khi truy cập trang chủ
@app.get("/")
def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found in server directory"}

# API cung cấp toàn bộ danh sách kèo từ picks.json cho Frontend
@app.get("/api/daily-picks")
def get_daily_picks():
    try:
        if os.path.exists("picks.json"):
            with open("picks.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        return []
    except Exception as e:
        return {"error": str(e)}