from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, Trade, Holding, SentimentStat
import datetime

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/positions")
def get_positions(db: Session = Depends(get_db)):
    return db.query(Holding).all()


@app.get("/pnl/daily")
def daily_pnl(db: Session = Depends(get_db)):
    today = datetime.date.today()
    start = datetime.datetime.combine(today, datetime.time.min)
    end = datetime.datetime.combine(today, datetime.time.max)
    pnl = db.query(func.sum(Trade.profit_loss)).filter(Trade.timestamp.between(start, end)).scalar() or 0
    return {"date": str(today), "pnl": pnl}


@app.get("/pnl/total")
def total_pnl(db: Session = Depends(get_db)):
    pnl = db.query(func.sum(Trade.profit_loss)).scalar() or 0
    return {"pnl": pnl}


@app.get("/trends")
def get_trends(db: Session = Depends(get_db)):
    trades = db.query(Trade).order_by(Trade.timestamp.desc()).limit(50).all()
    return [
        {"symbol": t.symbol, "type": t.trade_type, "timestamp": t.timestamp}
        for t in trades
    ]


@app.get("/stats/sentiment")
def sentiment_stats(db: Session = Depends(get_db)):
    stats = db.query(SentimentStat).all()
    return stats
