import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/trading",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    order_id = Column(String, index=True)
    symbol = Column(String)
    trade_type = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Integer)
    profit_loss = Column(Float)
    profit_loss_pct = Column(Float)
    status = Column(String)
    strategy = Column(String)
    rationale = Column(String)
    is_paper = Column(Boolean, default=False)

class Holding(Base):
    __tablename__ = "holdings"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

class Fund(Base):
    __tablename__ = "funds"
    id = Column(Integer, primary_key=True, default=1)
    cash = Column(Float)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class SentimentStat(Base):
    __tablename__ = "sentiment_stats"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    sector = Column(String)
    sentiment = Column(String)
    trend = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def log_trade_db(details: dict):
    session = SessionLocal()
    try:
        trade = Trade(
            timestamp=details.get("Timestamp", datetime.datetime.utcnow()),
            order_id=details.get("OrderID"),
            symbol=details.get("Symbol"),
            trade_type=details.get("TradeType"),
            entry_price=details.get("EntryPrice"),
            exit_price=details.get("ExitPrice"),
            quantity=details.get("Quantity"),
            profit_loss=details.get("ProfitLoss"),
            profit_loss_pct=details.get("ProfitLoss_Pct"),
            status=details.get("Status"),
            strategy=details.get("Strategy"),
            rationale=details.get("Rationale"),
            is_paper=str(details.get("OrderID", "")).startswith("PAPER_")
        )
        session.add(trade)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def sync_holdings(kite):
    """Fetches portfolio holdings and cash and persists them."""
    session = SessionLocal()
    try:
        holdings = kite.holdings() if hasattr(kite, 'holdings') else []
        session.query(Holding).delete()
        for h in holdings:
            session.add(Holding(symbol=h.get('tradingsymbol'), quantity=h.get('quantity'), avg_price=h.get('average_price')))
        margins = kite.margins() if hasattr(kite, 'margins') else {}
        cash = margins.get('equity', {}).get('available', {}).get('live_balance')
        session.query(Fund).delete()
        session.add(Fund(cash=cash))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
