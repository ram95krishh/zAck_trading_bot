# Environment Setup

This guide walks through setting up the Python trading engine, API server, and React dashboard.

## Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL running locally or remotely
- *(Optional)* TA-Lib system libraries if you prefer the native TA-Lib implementation for indicators

### Installing TA-Lib (optional)
- **macOS (Homebrew):** `brew install ta-lib`
- **Debian/Ubuntu:** `sudo apt-get install ta-lib`
- **RHEL/CentOS:** `sudo yum install ta-lib`

If TA-Lib is not installed, the project automatically falls back to [`pandas-ta`](https://github.com/twopirllc/pandas-ta) for indicator calculations.

## Python Backend
### 1. Clone and create a virtual environment
```bash
git clone https://github.com/zackakshayy/zAck_trading_bot.git
cd zAck_trading_bot
python3 -m venv trade_bot
source trade_bot/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```
After installing the system libraries above you can enable the optional TA-Lib backend:
```bash
pip install TA-Lib
```

### 3. Start PostgreSQL (Docker Compose option)
If you do not already have a PostgreSQL instance, the repository ships with a Compose file and helper script. This spins up a local database that listens on port `5432`.

```bash
scripts/start_db.sh
```

You can override the default credentials by exporting `POSTGRES_DB`, `POSTGRES_USER`, or `POSTGRES_PASSWORD` before running the script. Logs are available via `docker compose logs -f db`.

### 4. Configure the application
- Copy `config.example.yaml` to `config.yaml` and fill in API keys and trading flags.
- Set the `DATABASE_URL` environment variable pointing to your PostgreSQL instance, e.g.:
  ```bash
  export DATABASE_URL=postgresql+psycopg://user:pass@host/dbname
  ```

### 5. Initialize the database
```bash
python init_db.py
```

### 6. Run the trading engine
```bash
python trading_bot.py
```

### 7. Run the API server (optional, for REST endpoints)
Open a new terminal, activate the virtual environment, and start `uvicorn`:
```bash
uvicorn api:app --reload
```

## React Frontend
### 1. Install packages
```bash
cd frontend
npm install
```

### 2. Set the API base URL if different from `http://localhost:8000`
Create a `.env` file with:
```
VITE_API_URL=http://<host>:<port>
```

### 3. Start the development server
```bash
npm run dev
```

Visit the printed URL to access the dashboard.
