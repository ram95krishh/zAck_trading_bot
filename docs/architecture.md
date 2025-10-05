# Engine Architecture

This diagram illustrates the high-level components of the trading engine and how they interact.

```mermaid
flowchart LR
    T["trading_bot.py\nOrchestrator"] --> MC["MarketConditionIdentifier\nmarket_context.py"]
    T --> SA["SentimentAgent\nsentiment_agent.py"]
    T --> LGA["LangGraphAgent\nlanggraph_agent.py"]
    LGA -->|"strategy + analysis"| OAI[("OpenAI API")]
    T --> OE["OrderExecutionAgent\nagents.py"]
    T --> PM["PositionManagementAgent\nagents.py"]
    OE --> KC[("Zerodha KiteConnect")]
    PM --> KC
    T --> DB[("PostgreSQL Database\ndatabase.py")] 
    SA --> NEWS[("NewsAPI / TextBlob")]
    T --> API["FastAPI\napi.py"]
    API --> UI["React Dashboard"]
```

The orchestrator coordinates agents, which communicate with external services like Zerodha, OpenAI, and NewsAPI. All trades, holdings, and sentiment statistics are persisted in PostgreSQL and surfaced through a FastAPI backend to a React dashboard.

