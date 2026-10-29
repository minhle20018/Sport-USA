from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI(title="VMAH US Sports AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "sqlite:///sports_bettor.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

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
    updated_at = Column(DateTime)

@app.get("/api/daily-picks")
def get_daily_picks():
    session = SessionLocal()
    predictions = session.query(MatchPrediction).all()
    session.close()
    
    results = []
    for p in predictions:
        results.append({
            "sport": p.sport or "US Sport",
            "home_team": p.home_team,
            "away_team": p.away_team,
            "bookmaker": p.bookmaker,
            "home_odds": p.home_odds,
            "away_odds": p.away_odds,
            "ai_home_prob": round(p.ai_home_prob * 100, 1) if p.ai_home_prob else 0.0,
            "ai_away_prob": round(p.ai_away_prob * 100, 1) if p.ai_away_prob else 0.0,
            "edge_home": round(p.edge_home * 100, 1) if p.edge_home else 0.0,
            "edge_away": round(p.edge_away * 100, 1) if p.edge_away else 0.0,
            "recommendation": p.recommendation or "Neutral Pick",
            "ou_line": p.ou_line or 215.5,
            "ai_predicted_total": p.ai_predicted_total or 218.0,
            "ou_recommendation": p.ou_recommendation or "🔥 TÀI (OVER)",
            "commence_time": str(p.commence_time) if p.commence_time else "Live"
        })
    return results