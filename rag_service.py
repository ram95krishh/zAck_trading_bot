import logging
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from database import SessionLocal, Trade


class RAGService:
    """Utility class to provide retrieval-augmented context for AI features.

    The service loads historical trades from the database and prepares
    textual context snippets for strategy selection and loss analysis
    routines.  If the database is empty, empty strings are returned so the
    caller can fall back gracefully.
    """

    def __init__(self, config: dict):
        self.config = config
        # retained for backwards compatibility with previous file-based logs
        self.trade_log_path = "unused"

    # ------------------------------------------------------------------
    def _load_data(self, _path: str) -> pd.DataFrame:
        """Load historical trades from the database into a DataFrame."""
        session: Session = SessionLocal()
        try:
            trades = session.query(Trade).order_by(Trade.timestamp).all()
            if not trades:
                return pd.DataFrame()
            records: list[dict[str, Any]] = [
                {
                    "Timestamp": t.timestamp,
                    "OrderID": t.order_id,
                    "Symbol": t.symbol,
                    "TradeType": t.trade_type,
                    "EntryPrice": t.entry_price,
                    "ExitPrice": t.exit_price,
                    "Quantity": t.quantity,
                    "ProfitLoss": t.profit_loss,
                    "Strategy": t.strategy,
                    "Rationale": t.rationale,
                }
                for t in trades
            ]
            return pd.DataFrame.from_records(records)
        except Exception:
            logging.exception("Failed to load trades for RAG context")
            return pd.DataFrame()
        finally:
            session.close()

    # ------------------------------------------------------------------
    def retrieve_context_for_strategy_selection(self, todays_conditions: str) -> str:
        """Return a short text summary of recent trades for strategy selection."""
        df = self._load_data(self.trade_log_path)
        if df.empty:
            return ""
        recent = df.tail(20)[["Timestamp", "Symbol", "TradeType", "Strategy", "ProfitLoss"]]
        context = recent.to_string(index=False)
        return (
            f"Recent trades:\n{context}\n"
            f"Today's market conditions: {todays_conditions}"
        )

    # ------------------------------------------------------------------
    def retrieve_context_for_loss_analysis(self, trade_details: dict) -> str:
        """Return context related to previous trades on the same symbol."""
        df = self._load_data(self.trade_log_path)
        if df.empty:
            return ""
        symbol = trade_details.get("Symbol")
        if symbol:
            df = df[df["Symbol"] == symbol]
        recent = df.tail(5)[["Timestamp", "TradeType", "EntryPrice", "ExitPrice", "ProfitLoss", "Strategy"]]
        return recent.to_string(index=False)
