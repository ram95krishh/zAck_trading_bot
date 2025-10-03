# zAck Trading Bot 3.0: An AI-Powered Algorithmic Trading System

zAck Trading Bot is a sophisticated, event-driven, and modular algorithmic trading
application designed for the Indian stock market (NIFTY 50). It leverages modern AI,
including Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG), to
make intelligent, data-driven trading decisions.

## Key Features
- Automated F&O trading via the Zerodha Kite Connect API
- Multi-strategy framework with a library of pre-built strategies
- AI-powered strategy selection using OpenAI models
- Retrieval-Augmented Generation (RAG) hooks for data-driven prompts
- Natural language prompting for user hints
- Dynamic strategy reassessment during market hours
- Real-time sentiment analysis with NewsAPI and TextBlob
- Economic event awareness through web scraping
- Paper trading mode for safe testing
- Automated email reporting
- FastAPI endpoints for portfolio, P&L, trade trends, and sentiment stats
- React + Vite dashboard for visualizing engine output

## Architecture Overview
The application is built on a modular, agent-based architecture designed for scalability and resilience.

### Orchestrator (`trading_bot.py`)
Central brain of the application managing the event loop and coordinating agents.

### Agents (`agents.py`)
- **OrderExecutionAgent** – handles order placement and communication with Kite
- **PositionManagementAgent** – manages active trades and risk controls

### Intelligence Layer
- **langgraph_agent.py** – interfaces with the OpenAI LLM to select strategies
- **sentiment_agent.py** – fetches and analyzes news for market sentiment
- **market_context.py** – identifies current market conditions

### Strategy & Indicators
- **strategy_factory.py** – library of trading strategies
- **indicator_calculator.py** & **indicators.py** – compute technical indicators

### Reporting & Persistence
- **database.py** – SQLAlchemy models for trades, holdings, funds, and sentiment stats
- **reporting.py** – generates and emails performance reports

For environment setup and detailed run instructions, see [config.md](config.md).

For a high-level architecture diagram of the engine, visit [docs/architecture.md](docs/architecture.md).

## Disclaimer
This software is provided for educational and experimental purposes only. Algorithmic
trading involves substantial risk and is not suitable for all investors. The authors
and contributors are not responsible for any financial losses incurred through the
use of this software. Always test thoroughly in paper trading mode before deploying
with real capital.
