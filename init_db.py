import logging

logging.basicConfig(level=logging.INFO)

from database import init_db

if __name__ == "__main__":
    try:
        init_db()
        print("Database initialized.")
    except Exception:
        logging.exception("Failed to initialize database")
        raise
