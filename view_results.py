import sqlite3
import pandas as pd

# Kết nối tới database SQLite đã lưu
conn = sqlite3.connect("sports_bettor.db")

# Truy vấn bảng kết quả dự đoán trận đấu
query = """
SELECT home_team, away_team, bookmaker, home_odds, away_odds, 
       ROUND(ai_home_prob * 100, 1) as ai_home_pct, 
       ROUND(edge_home * 100, 1) as edge_home_pct, 
       recommendation 
FROM match_predictions
"""
df = pd.read_sql_query(query, conn)
conn.close()

# Hiển thị toàn bộ kết quả dạng bảng rõ ràng
print("\n--- KẾT QUẢ PHÂN TÍCH AI & VALUE BETS HÔM NAY ---")
if df.empty:
    print("Chưa có dữ liệu trận đấu nào trong database.")
else:
    print(df.to_string(index=False))