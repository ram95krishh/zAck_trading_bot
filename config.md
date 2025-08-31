# Environment Setup

This guide explains how to configure both the trading engine and the accompanying React dashboard.

## Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL running locally or remotely
- TA-Lib system libraries (`apt-get install -y ta-lib-dev` on Debian/Ubuntu)

## Python Backend
1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/zackakshayy/zAck_trading_bot.git
   cd zAck_trading_bot
   python3 -m venv trade_bot
   source trade_bot/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Provide a `config.yaml` in the project root. Use `config.example.yaml` as a template for API keys and trading flags.
4. Initialize the database (PostgreSQL connection is configured via `DATABASE_URL` and uses the psycopg v3 driver, e.g. `postgresql+psycopg://user:pass@host/db`):
   ```bash
   python - <<'PY'
from database import init_db
init_db()
PY
   ```
5. Launch the trading engine:
   ```bash
   python trading_bot.py
   ```
6. To expose REST endpoints, run:
   ```bash
   uvicorn api:app --reload
   ```

## React Frontend
1. Navigate to the frontend folder and install packages:
   ```bash
   cd frontend
   npm install
   ```
2. Set the API base URL if different from `http://localhost:8000`:
   - Create a `.env` file with `VITE_API_URL=http://<host>:<port>`
3. Start the development server:
   ```bash
   npm run dev
   ```

Visit the printed URL to access the dashboard.
