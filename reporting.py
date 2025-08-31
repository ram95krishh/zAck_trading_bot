import logging
import datetime
from sqlalchemy import func
from database import SessionLocal, init_db, log_trade_db, Trade
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib


def initialize_trade_log():
    """Initializes database tables."""
    init_db()


def log_trade(trade_details):
    """Persist a trade to the database."""
    try:
        if trade_details.get('EntryPrice') and trade_details.get('Quantity'):
            pnl_pct = (trade_details.get('ProfitLoss', 0) /
                       (trade_details['EntryPrice'] * trade_details['Quantity'])) * 100
            trade_details['ProfitLoss_Pct'] = round(pnl_pct, 2)
        else:
            trade_details['ProfitLoss_Pct'] = 0.0
        log_trade_db(trade_details)
        logging.info(f"Successfully logged trade for {trade_details.get('Symbol')}")
    except Exception as e:
        logging.error(f"Failed to log trade: {e}", exc_info=True)


def send_daily_report(config, date_str, no_trades_reason=None):
    email_conf = config.get('email_settings', {})
    if not email_conf.get('send_daily_report', False):
        logging.info("Email reporting is disabled.")
        return
    session = SessionLocal()
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        start = datetime.datetime.combine(date_obj, datetime.time.min)
        end = datetime.datetime.combine(date_obj, datetime.time.max)
        trades = session.query(Trade).filter(Trade.timestamp.between(start, end)).all()
        if no_trades_reason:
            body = f"<p><strong>No trades were placed today. Reason:</strong> {no_trades_reason}</p>"
            live_pnl = paper_pnl = None
        else:
            live = [t for t in trades if not t.is_paper]
            paper = [t for t in trades if t.is_paper]
            live_pnl = sum(t.profit_loss or 0 for t in live)
            paper_pnl = sum(t.profit_loss or 0 for t in paper)
            body = _render_trades(live, paper)
        subject_parts = [f"Trading Report for {date_obj.strftime('%d %b, %Y')}"]
        if live_pnl is not None:
            subject_parts.append(f"Live P/L: {live_pnl:,.2f}")
        if paper_pnl is not None:
            subject_parts.append(f"Paper P/L: {paper_pnl:,.2f}")
        msg = MIMEMultipart()
        msg['From'] = email_conf.get('sender_email')
        msg['To'] = email_conf.get('receiver_email')
        msg['Subject'] = " | ".join(subject_parts)
        msg.attach(MIMEText(f"<html><body>{body}</body></html>", 'html'))
        with smtplib.SMTP(email_conf['smtp_server'], email_conf['smtp_port']) as server:
            server.starttls()
            server.login(email_conf['sender_email'], email_conf['sender_password'])
            server.send_message(msg)
        logging.info("Successfully sent daily email report.")
    except Exception as e:
        logging.error(f"Failed to send daily report: {e}", exc_info=True)
    finally:
        session.close()


def _render_trades(live, paper):
    def table(rows, title):
        if not rows:
            return f"<h3>{title}</h3><p>No trades were executed in this mode today.</p>"
        total_pnl = sum(t.profit_loss or 0 for t in rows)
        wins = sum(1 for t in rows if (t.profit_loss or 0) > 0)
        losses = len(rows) - wins
        win_rate = (wins / len(rows) * 100) if rows else 0
        header = f"<h3>{title}</h3><p>Total P/L: {total_pnl:,.2f} | Win Rate: {win_rate:.2f}%</p>"
        rows_html = "".join([
            f"<tr><td>{t.symbol}</td><td>{t.trade_type}</td><td>{t.entry_price:.2f}</td><td>{t.exit_price:.2f}</td><td>{t.quantity}</td><td>{t.profit_loss:.2f}</td></tr>"
            for t in rows])
        table_html = f"<table border='1'><tr><th>Symbol</th><th>Type</th><th>Entry</th><th>Exit</th><th>Qty</th><th>P/L</th></tr>{rows_html}</table>"
        return header + table_html
    return table(live, "Live Trades Summary") + "<hr>" + table(paper, "Paper Trades Summary")


def send_monthly_report(config, date_str):
    email_conf = config.get('email_settings', {})
    if not email_conf.get('send_daily_report', False):
        return
    session = SessionLocal()
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        start = datetime.datetime(date_obj.year, date_obj.month, 1)
        end = datetime.datetime(date_obj.year, date_obj.month, 1) + datetime.timedelta(days=32)
        end = end.replace(day=1)
        trades = session.query(Trade).filter(Trade.timestamp >= start, Trade.timestamp < end).all()
        total_pnl = sum(t.profit_loss or 0 for t in trades)
        body = f"<p>Total P/L for {date_obj.strftime('%B %Y')}: {total_pnl:,.2f}</p>"
        msg = MIMEMultipart()
        msg['From'] = email_conf.get('sender_email')
        msg['To'] = email_conf.get('receiver_email')
        msg['Subject'] = f"Monthly Trading Summary: {date_obj.strftime('%B %Y')}"
        msg.attach(MIMEText(f"<html><body>{body}</body></html>", 'html'))
        with smtplib.SMTP(email_conf['smtp_server'], email_conf['smtp_port']) as server:
            server.starttls()
            server.login(email_conf['sender_email'], email_conf['sender_password'])
            server.send_message(msg)
        logging.info("Successfully sent monthly report.")
    except Exception as e:
        logging.error(f"Failed to send monthly report: {e}", exc_info=True)
    finally:
        session.close()
