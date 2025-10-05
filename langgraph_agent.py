import logging
import asyncio
import datetime
from datetime import timezone
from openai import AsyncOpenAI, RateLimitError
from rag_service import RAGService

class LangGraphAgent:
    """AI agent using OpenAI's models to recommend a strategy from a full suite."""
    def __init__(self, config, rag_service: RAGService):
        self.config = config
        self.rag_service = rag_service
        api_key = config.get('openai', {}).get('api_key', "")
        # Disable the SDK's automatic retries so our manual backoff controls pacing
        self.client = (
            AsyncOpenAI(api_key=api_key, max_retries=0) if api_key else None
        )
        self.model_name = "gpt-4o-mini"
        self._last_recommendation = None
        self._last_call_time = None
        self._next_call_time = None

    async def get_recommended_strategy(self, market_conditions: set, user_prompt: str = None, rag_context: str = None):
        """
        Gets a strategy recommendation from the OpenAI API, optionally augmented with
        RAG context.
        """
        if not self.client:
            logging.error("[OpenAI Agent] OpenAI API key not found. Defaulting strategy.")
            return "OpenAI_Default"

        logging.info(f"[OpenAI Agent] Market Conditions: {market_conditions}. Recommending strategy...")

        reassess_minutes = self.config['trading_flags'].get(
            'strategy_reassessment_period_minutes', 30
        )
        now = datetime.datetime.now(timezone.utc)

        # Respect any cooldown from a previous rate-limit hit
        if self._next_call_time and now < self._next_call_time:
            wait_for = (self._next_call_time - now).total_seconds()
            logging.info(
                f"[OpenAI Agent] Waiting {wait_for:.1f}s before next recommendation call"
            )
            await asyncio.sleep(wait_for)
            now = datetime.datetime.now(timezone.utc)

        if (
            self._last_recommendation
            and self._last_call_time
            and now - self._last_call_time < datetime.timedelta(minutes=reassess_minutes)
        ):
            logging.info("[OpenAI Agent] Using cached strategy recommendation")
            return self._last_recommendation

        prompt_sections = [
            "You are an expert intraday options trading strategist for the Indian NIFTY 50 index.",
            "Your task is to select the single best strategy for today based on the provided data.",
            f"\n**Today's Market Conditions:** {', '.join(market_conditions)}",
        ]
        
        # --- FIX: Conditionally add the RAG context to the prompt ---
        if rag_context:
            logging.info("[OpenAI Agent] Using RAG context for strategy selection.")
            prompt_sections.append(f"\n**RAG Context (Historical Performance):**\n{rag_context}")
        else:
            logging.info("[OpenAI Agent] Bypassing RAG context for strategy selection.")

        if user_prompt:
            prompt_sections.append(f"\n**User's Preference/Observation:** '{user_prompt}'")

        prompt_sections.append("\n**Available Strategies (and their primary purpose):**")
        prompt_sections.append(
            """
1.  **'OpenAI_Default'**: A balanced, multi-indicator strategy (CPR, EMA, RSI Divergence).
2.  **'Supertrend_MACD'**: A strong trend-following strategy.
3.  **'Volatility_Cluster_Reversal'**: A counter-trend strategy for high volatility.
4.  **'Volume_Spread_Analysis'**: Detects smart money activity.
5.  **'EMA_Cross_RSI'**: A classic, fast-acting momentum strategy.
6.  **'Momentum_VWAP_RSI'**: A momentum strategy using VWAP.
7.  **'Breakout_Prev_Day_HL'**: A breakout strategy on previous day's high/low.
8.  **'Opening_Range_Breakout'**: A classic ORB strategy.
9.  **'BB_Squeeze_Breakout'**: A volatility breakout strategy.
10. **'MA_Crossover'**: A simple moving average crossover strategy.
11. **'RSI_Divergence'**: A pure reversal strategy on RSI divergence.
12. **'Reversal_Detector'**: A specialized reversal strategy for overextended trends.
"""
        )
        prompt_sections.append("\nBased on all the above information, which single strategy name from the list has the highest probability of success today? Return only the name.")
        
        prompt = "\n".join(prompt_sections)

        try:
            backoff = 15
            while True:
                try:
                    response = await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    headers = getattr(getattr(response, "response", None), "headers", {})
                    if headers:
                        logging.debug(f"[OpenAI Agent] Response headers: {headers}")
                    if getattr(response, "usage", None):
                        logging.info(
                            f"[OpenAI Agent] Usage - prompt: {response.usage.prompt_tokens}, total: {response.usage.total_tokens}"
                        )
                    break
                except RateLimitError as e:
                    headers = getattr(getattr(e, "response", None), "headers", {})
                    logging.warning(
                        f"[OpenAI Agent] Rate limit hit. Headers: {headers}"
                    )
                    remaining_req = headers.get("x-ratelimit-remaining-requests")
                    remaining_tok = headers.get("x-ratelimit-remaining-tokens")
                    if remaining_req == "0" and (remaining_tok and remaining_tok != "0"):
                        logging.warning("[OpenAI Agent] Request rate limit exceeded.")
                    if remaining_tok == "0":
                        logging.warning("[OpenAI Agent] Token quota exceeded.")
                    retry_after = headers.get("retry-after")
                    sleep_for = float(retry_after) if retry_after else backoff
                    # Record cooldown to throttle subsequent calls
                    self._next_call_time = datetime.datetime.now(timezone.utc) + datetime.timedelta(seconds=sleep_for)
                    await asyncio.sleep(sleep_for)
                    backoff = min(backoff * 2, 300)
                except Exception:
                    raise
            recommended_strategy = (
                response.choices[0].message.content.strip().replace("'", "").split('\n')[-1]
            )

            valid_strategies = [
                "OpenAI_Default", "Supertrend_MACD", "Volatility_Cluster_Reversal",
                "Volume_Spread_Analysis", "EMA_Cross_RSI", "Momentum_VWAP_RSI",
                "Breakout_Prev_Day_HL", "Opening_Range_Breakout", "BB_Squeeze_Breakout",
                "MA_Crossover", "RSI_Divergence", "Reversal_Detector"
            ]
            if recommended_strategy not in valid_strategies:
                logging.warning(f"[OpenAI Agent] LLM recommended unknown strategy: '{recommended_strategy}'. Defaulting.")
                recommended_strategy = "OpenAI_Default"

            logging.info(f"[OpenAI Agent] AI Recommended Strategy: {recommended_strategy}")
            self._last_recommendation = recommended_strategy
            self._last_call_time = now
            return recommended_strategy

        except Exception as e:
            logging.error(f"[OpenAI Agent] Error calling OpenAI API: {e}. Defaulting to OpenAI_Default.")
            return "OpenAI_Default"
