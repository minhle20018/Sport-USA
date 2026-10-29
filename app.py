from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="VMAH US Sports AI Backend")

# Cấu hình CORS để cho phép frontend gọi API thoải mái
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Định nghĩa đường dẫn gốc để trả về giao diện index.html trên Render
@app.get("/")
def read_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found in server directory"}

# 2. API cung cấp dữ liệu danh sách kèo hàng ngày cho Frontend
@app.get("/api/daily-picks")
def get_daily_picks():
    # Dữ liệu mẫu hoặc dữ liệu kết nối từ database / file JSON của bot
    # Ở đây FastAPI sẽ trả về JSON chứa danh sách các trận đấu, tỷ lệ AI và nhãn VIP/Neutral
    try:
        # Nếu bạn lưu dữ liệu trong file picks.json do worker tạo ra:
        if os.path.exists("picks.json"):
            import json
            with open("picks.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        
        # Dữ liệu fallback nếu chưa có file picks.json
        return [
            {
                "sport": "BASKETBALL_NBA",
                "commence_time": "2026-10-29 23:10:00",
                "bookmaker": "FanDuel",
                "home_team": "Atlanta Hawks",
                "away_team": "Miami Heat",
                "ai_home_prob": 60.0,
                "ai_away_prob": 40.0,
                "edge_home": 4.1,
                "edge_away": -4.1,
                "recommendation": "⭐ VIP PICK: Atlanta Hawks",
                "ou_line": 215.5,
                "ai_predicted_total": 219.0,
                "ou_recommendation": "🔥 TÀI (OVER) 215.5"
            }
        ]
    except Exception as e:
        return {"error": str(e)}