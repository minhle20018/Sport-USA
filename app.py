@app.get("/api/daily-picks")
def get_daily_picks():
    try:
        db_path = "sports_bettor.db"
        if not os.path.exists(db_path):
            return []
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Tự động tìm tên bảng đầu tiên có trong database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            conn.close()
            return []
        
        table_name = tables[0][0] # Lấy tên bảng đầu tiên
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        return {"error": str(e)}