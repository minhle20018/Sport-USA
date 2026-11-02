@app.get("/api/stats")
def get_betting_stats():
    conn = sqlite3.connect("sports_bettor.db")
    cursor = conn.cursor()
    
    # Đếm tổng số trận Finished có kết quả WIN hoặc LOSE
    cursor.execute("SELECT COUNT(*) FROM match_predictions WHERE result_status = 'WIN'")
    total_wins = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT COUNT(*) FROM match_predictions WHERE result_status = 'LOSE'")
    total_losses = cursor.fetchone()[0] or 0
    
    total_settled = total_wins + total_losses
    win_rate = (total_wins / total_settled * 100) if total_settled > 0 else 0.0
    
    conn.close()
    return {
        "total_wins": total_wins,
        "total_losses": total_losses,
        "total_settled": total_settled,
        "win_rate": round(win_rate, 1)
    }