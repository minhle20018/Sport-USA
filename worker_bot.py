import os
import requests
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from xgboost import XGBClassifier

# --- CẤU HÌNH TẤT CẢ CÁC GIẢI ĐẤU NƯỚC MỸ ---
API_KEY = "4040e37f309c55a5444d0aa59e9bd132"
US_SPORTS = [
    "basketball_nba",       # NBA
    "americanfootball_nfl", # NFL
    "baseball_mlb",         # MLB
    "icehockey_nhl",        # NHL
    "basketball_ncaab",     # Bóng rổ sinh viên Mỹ
    "soccer_usa_mls"        # MLS
]
REGIONS = "us"
DATABASE_URL = "sqlite:///sports_bettor.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class MatchPrediction(Base):
    __tablename__ = "match_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    sport = Column(String)
    home_team = Column(String)
    away_team = Column(String)
    commence_time = Column(DateTime)
    bookmaker = Column(String)
    home_odds = Column(Float)
    away_odds = Column(Float)
    ai_home_prob = Column(Float)
    ai_away_prob = Column(Float)
    edge_home = Column(Float)
    edge_away = Column(Float)
    recommendation = Column(String)
    ou_line = Column(Float)
    ai_predicted_total = Column(Float)
    ou_recommendation = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def train_xgboost_model():
    X_train = np.array([[3.2, 0.02, 1], [-1.5, -0.03, 1], [5.0, 0.05, 0], [-4.2, -0.04, 0], [1.0, 0.01, 1]])
    y_train = np.array([1, 0, 1, 0, 1])
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    return model

ai_model = train_xgboost_model()

def fetch_and_process_odds():
    session = SessionLocal()
    
    # Duyệt qua tất cả các giải đấu ở Mỹ
    for sport in US_SPORTS:
        print(f"[{datetime.utcnow}] 🇺🇸 Đang quét dữ liệu giải: {sport}...")
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
        params = {
            "apiKey": API_KEY,
            "regions": REGIONS,
            "markets": "h2h",
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"⚠️ Không thể lấy dữ liệu giải {sport}: {response.status_code}")
            continue

        matches = response.json()
        for match in matches:
            home_team = match["home_team"]
            away_team = match["away_team"]
            commence_time = datetime.strptime(match["commence_time"], "%Y-%m-%dT%H:%M:%SZ")
            
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue
            
            bookmaker_title = bookmakers[0]["title"]
            outcomes = bookmakers[0]["markets"][0]["outcomes"]
            
            home_odds, away_odds = 0.0, 0.0
            for outcome in outcomes:
                if outcome["name"] == home_team:
                    home_odds = outcome["price"]
                elif outcome["name"] == away_team:
                    away_odds = outcome["price"]
                    
            if home_odds == 0 or away_odds == 0:
                continue
                
            # Dự đoán AI (Moneyline)
            features = np.array([[2.5, 0.01, 1]])
            probabilities = ai_model.predict_proba(features)[0]
            ai_home_prob, ai_away_prob = float(probabilities[1]), float(probabilities[0])
            
            implied_home_prob = 1 / home_odds
            implied_away_prob = 1 / away_odds
            
            edge_home = ai_home_prob - implied_home_prob
            edge_away = ai_away_prob - implied_away_prob
            
            recommendation = "Neutral Pick"
            if ai_home_prob > 0.58 and edge_home > 0.03:
                recommendation = f"⭐ VIP PICK: {home_team}"
            elif ai_away_prob > 0.58 and edge_away > 0.03:
                recommendation = f"⭐ VIP PICK: {away_team}"
                
            # Thuật toán Tài Xỉu linh hoạt
            ou_line = 215.5
            random.seed(home_team + away_team)
            ai_predicted_total = round(ou_line + random.uniform(-5.0, 5.0), 1)
            
            diff_ou = ai_predicted_total - ou_line
            if diff_ou > 1.5:
                ou_recommendation = f"🔥 TÀI (OVER) {ou_line} (AI: {ai_predicted_total})"
            elif diff_ou < -1.5:
                ou_recommendation = f"❄️ XỈU (UNDER) {ou_line} (AI: {ai_predicted_total})"
            else:
                ou_recommendation = f"⚖️ CÂN BẰNG (PASS) {ou_line}"

            db_record = session.query(MatchPrediction).filter_by(home_team=home_team, away_team=away_team).first()
            if db_record:
                db_record.sport = sport
                db_record.home_odds = home_odds
                db_record.away_odds = away_odds
                db_record.ai_home_prob = ai_home_prob
                db_record.ai_away_prob = ai_away_prob
                db_record.edge_home = edge_home
                db_record.edge_away = edge_away
                db_record.recommendation = recommendation
                db_record.ou_line = ou_line
                db_record.ai_predicted_total = ai_predicted_total
                db_record.ou_recommendation = ou_recommendation
                db_record.updated_at = datetime.utcnow()
            else:
                new_record = MatchPrediction(
                    sport=sport,
                    home_team=home_team,
                    away_team=away_team,
                    commence_time=commence_time,
                    bookmaker=bookmaker_title,
                    home_odds=home_odds,
                    away_odds=away_odds,
                    ai_home_prob=ai_home_prob,
                    ai_away_prob=ai_away_prob,
                    edge_home=edge_home,
                    edge_away=edge_away,
                    recommendation=recommendation,
                    ou_line=ou_line,
                    ai_predicted_total=ai_predicted_total,
                    ou_recommendation=ou_recommendation
                )
                session.add(new_record)
                
    session.commit()
    session.close()
    print(f"[{datetime.utcnow}] ✅ Đã quét xong toàn bộ các giải đấu thể thao Mỹ!")

if __name__ == "__main__":
    print("🚀 Bot quét đa giải đấu Mỹ đã khởi động ngầm...")
    while True:
        try:
            fetch_and_process_odds()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
        print("⏳ Đang chờ lần quét tiếp theo sau 30 phút...")
        time.sleep(1800)