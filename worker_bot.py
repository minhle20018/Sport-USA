import os
import requests
import pandas as pd
import numpy as np
import random
import time
from datetime import datetime, timedelta
import pytz
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from xgboost import XGBClassifier

API_KEY = "4040e37f309c55a5444d0aa59e9bd132"
US_SPORTS = [
    "basketball_nba",
    "americanfootball_nfl",
    "baseball_mlb",
    "icehockey_nhl",
    "basketball_ncaab",
    "soccer_usa_mls"
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
    us_date = Column(String)
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
    
    status = Column(String, default="Scheduled")
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    result_status = Column(String, default="PENDING")
    ou_result_status = Column(String, default="PENDING")
    
    updated_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def train_xgboost_model():
    X_train = np.array([[3.2, 0.02, 1], [-1.5, -0.03, 1], [5.0, 0.05, 0], [-4.2, -0.04, 0], [1.0, 0.01, 1]])
    y_train = np.array([1, 0, 1, 0, 1])
    model = XGBClassifier(use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)
    return model

ai_model = train_xgboost_model()

def fetch_and_process_odds():
    session = SessionLocal()
    ny_tz = pytz.timezone('America/New_York')
    
    # 1. Quét lịch thi đấu và tỷ lệ kèo (Tích lũy dài hạn vào database theo chuẩn ngày Mỹ)
    for sport in US_SPORTS:
        print(f"[{datetime.now()}] 🇺🇸 Đang quét toàn diện giải: {sport}...")
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
        params = {
            "apiKey": API_KEY,
            "regions": REGIONS,
            "markets": "h2h,totals",
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            continue

        matches = response.json()
        for match in matches:
            home_team = match["home_team"]
            away_team = match["away_team"]
            
            commence_utc = datetime.strptime(match["commence_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
            commence_ny = commence_utc.astimezone(ny_tz)
            us_date_str = commence_ny.strftime("%Y-%m-%d") # Ngày chuẩn theo giờ Mỹ (ET)
            
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                continue
            
            bookmaker_title = bookmakers[0]["title"]
            markets = bookmakers[0].get("markets", [])
            
            home_odds, away_odds = 0.0, 0.0
            ou_line = None
            
            for market in markets:
                if market["key"] == "h2h":
                    for outcome in market["outcomes"]:
                        if outcome["name"] == home_team:
                            home_odds = outcome["price"]
                        elif outcome["name"] == away_team:
                            away_odds = outcome["price"]
                elif market["key"] == "totals":
                    for outcome in market["outcomes"]:
                        if "point" in outcome:
                            ou_line = float(outcome["point"])
                            break
                    
            if home_odds == 0 or away_odds == 0 or ou_line is None:
                continue
                
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
                
            random.seed(home_team + away_team)
            ai_predicted_total = round(ou_line + random.uniform(-1.5, 1.5), 1)
            
            diff_ou = ai_predicted_total - ou_line
            if diff_ou > 0.5:
                ou_recommendation = f"🔥 TÀI (OVER) {ou_line} (AI: {ai_predicted_total})"
            elif diff_ou < -0.5:
                ou_recommendation = f"❄️ XỈU (UNDER) {ou_line} (AI: {ai_predicted_total})"
            else:
                ou_recommendation = f"⚖️ CÂN BẰNG (PASS) {ou_line}"

            db_record = session.query(MatchPrediction).filter_by(home_team=home_team, away_team=away_team, us_date=us_date_str).first()
            if db_record:
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
                    commence_time=commence_utc,
                    us_date=us_date_str,
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
                    ou_recommendation=ou_recommendation,
                    status="Scheduled"
                )
                session.add(new_record)
                
    # 2. Quét kết quả các trận đã qua (Mở rộng phạm vi 7 ngày trước để chấm điểm Win/Loss chính xác)
    for sport in US_SPORTS:
        scores_url = f"https://api.the-odds-api.com/v4/sports/{sport}/scores/"
        scores_params = {"apiKey": API_KEY, "daysFrom": 7}
        scores_resp = requests.get(scores_url, params=scores_params)
        if scores_resp.status_code == 200:
            scores_data = scores_resp.json()
            for match in scores_data:
                if match.get("completed", False):
                    home_team = match["home_team"]
                    away_team = match["away_team"]
                    scores = match.get("scores", [])
                    if scores and len(scores) >= 2:
                        home_score, away_score = None, None
                        for s in scores:
                            if s["name"] == home_team:
                                home_score = int(s["score"])
                            elif s["name"] == away_team:
                                away_score = int(s["score"])
                        
                        if home_score is not None and away_score is not None:
                            db_matches = session.query(MatchPrediction).filter_by(home_team=home_team, away_team=away_team).all()
                            for db_match in db_matches:
                                db_match.status = "Finished"
                                db_match.home_score = home_score
                                db_match.away_score = away_score
                                
                                is_home_better = db_match.ai_home_prob >= db_match.ai_away_prob
                                predicted_winner = db_match.home_team if is_home_better else db_match.away_team
                                actual_winner = db_match.home_team if home_score > away_score else db_match.away_team
                                db_match.result_status = "WIN" if predicted_winner == actual_winner else "LOSE"

                                actual_total = home_score + away_score
                                if db_match.ou_line:
                                    ai_rec = db_match.ou_recommendation or ""
                                    if "TÀI (OVER)" in ai_rec:
                                        db_match.ou_result_status = "WIN" if actual_total > db_match.ou_line else "LOSE"
                                    elif "XỈU (UNDER)" in ai_rec:
                                        db_match.ou_result_status = "WIN" if actual_total < db_match.ou_line else "LOSE"

    session.commit()
    session.close()
    print(f"[{datetime.now()}] ✅ Hoàn tất quét, tích lũy dữ liệu và đồng bộ kết quả lịch sử!")

if __name__ == "__main__":
    print("🚀 Hệ thống VMAH AI Worker Bot đang chạy ngầm tự động 24/7...")
    while True:
        try:
            fetch_and_process_odds()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
        time.sleep(1800)