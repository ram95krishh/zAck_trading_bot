import logging
import pandas as pd
import pandas_ta as ta
import datetime
import asyncio
import re
from kiteconnect import KiteConnect, exceptions
from rag_service import RAGService

def _execute_order_sync(api_key: str, access_token: str, order_params: dict) -> str | None:
    """
    Creates an isolated KiteConnect instance to place a single order.
    This function is designed to be called via asyncio.to_thread.
    """
    try:
        logging.info("WORKER: Creating isolated KiteConnect instance for order.")
        kite_worker = KiteConnect(api_key=api_key)
        kite_worker.set_access_token(access_token)
        logging.info(f"WORKER: Placing order with params: {order_params}")
        order_id = kite_worker.place_order(**order_params)
        logging.info(f"WORKER: Order placed successfully. Order ID: {order_id}")
        return order_id
    except exceptions.InputException as e:
        logging.error(f"WORKER: InputException during order placement: {e}", exc_info=True)
    except exceptions.NetworkException as e:
        logging.error(f"WORKER: NetworkException during order placement: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"WORKER: An unexpected error occurred during order placement: {e}", exc_info=True)
    return None

class OrderExecutionAgent:
    """Handles order sizing, placement, and retrieval asynchronously."""
    def __init__(self, kite: KiteConnect, config: dict):
        self.kite = kite
        self.config = config
        self.flags = config['trading_flags']
        self.trading_budget = self.flags.get('trading_budget')
        self.nfo_instruments = pd.DataFrame(self.kite.instruments('NFO'))
        self.underlying_token = self._get_instrument_token(self.flags['underlying_instrument'], 'NSE')
        self._symbol_regex = re.compile(r"([A-Z]+)(\d{2})(\d{1,2})(\d{2})(\d{5})(CE|PE)$")

    def _get_instrument_token(self, name, exchange):
        """Helper to find instrument token."""
        try:
            instruments = self.kite.instruments(exchange)
            return [i['instrument_token'] for i in instruments if i['tradingsymbol'] == name][0]
        except (exceptions.DataException, exceptions.NetworkException) as e:
            logging.error(f"Failed to fetch instruments for {exchange}. Error: {e}")
            raise ConnectionError(f"Could not fetch instruments for {exchange}.")

    async def place_trade(self, direction):
        """
        Asynchronously prepares and dispatches an entry order to a worker thread.
        """
        symbol, qty = await self._get_trade_details(direction)
        if not symbol or not qty:
            return None
        
        order_params = {
            "variety": self.flags['order_variety'],
            "exchange": self.kite.EXCHANGE_NFO,
            "tradingsymbol": symbol,
            "transaction_type": self.kite.TRANSACTION_TYPE_BUY,
            "quantity": qty,
            "product": self.flags['product_type'],
            "order_type": self.kite.ORDER_TYPE_MARKET,
        }
        
        logging.info(
            f"ASYNC: Preparing to place LIVE entry order -> {order_params}"
        )
        
        try:
            api_key = self.config['zerodha']['api_key']
            access_token = self.config['zerodha']['access_token']
            
            order_id = await asyncio.to_thread(
                _execute_order_sync,
                api_key,
                access_token,
                order_params
            )
            
            if not order_id:
                logging.error(f"ASYNC: Order execution in worker thread failed for {symbol}.")
                return None

            logging.info(f"ASYNC: Successfully dispatched and executed order. Final Order ID: {order_id}")
            
            await asyncio.sleep(1)
            order_history = await asyncio.to_thread(self.kite.order_history, order_id)
            avg_price_list = [o['average_price'] for o in order_history if o['status'] == 'COMPLETE' and o.get('average_price', 0) > 0]
            
            avg_price = avg_price_list[0] if avg_price_list else 0
            if avg_price == 0:
                 trades = await asyncio.to_thread(self.kite.order_trades, order_id)
                 avg_price = trades[-1]['average_price'] if trades else 0

            if avg_price == 0:
                 raise Exception("Order executed but unable to fetch average price.")

            return {'order_id': order_id, 'symbol': symbol, 'quantity': qty, 'entry_price': avg_price, 'type': direction}

        except Exception as e:
            logging.error(f"ASYNC: Failed to dispatch order for {symbol}: {e}", exc_info=True)
            return None

    async def get_paper_trade_details(self, direction):
        symbol, qty = await self._get_trade_details(direction)
        if not symbol or not qty:
            return None
        try:
            ltp_data = await asyncio.to_thread(self.kite.ltp, f"NFO:{symbol}")
            ltp = ltp_data[f"NFO:{symbol}"]['last_price']
            desc = self._describe_option_symbol(symbol)
            logging.info(
                f"[Paper Trade] Signal to BUY {desc} ({symbol}) at {ltp:.2f} with Qty: {qty}"
            )
            return {
                'order_id': f"PAPER_{int(datetime.datetime.now().timestamp())}",
                'symbol': symbol,
                'quantity': qty,
                'entry_price': ltp,
                'type': direction,
            }
        except Exception as e:
            logging.error(f"Failed to get LTP for paper trade {symbol}: {e}")
            return None

    async def _get_trade_details(self, direction):
        try:
            ltp_data = await asyncio.to_thread(self.kite.ltp, str(self.underlying_token))
            ltp = ltp_data[str(self.underlying_token)]['last_price']
            
            atm_strike = round(ltp / 50) * 50
            option_type = 'CE' if direction == 'BUY' else 'PE'
            
            today = datetime.date.today()
            expiries = pd.to_datetime(
                self.nfo_instruments['expiry'], utc=True
            ).dt.tz_localize(None).dt.date
            possible_expiries = sorted([d for d in expiries.unique() if d >= today])
            
            if not possible_expiries:
                logging.warning("No future expiries found.")
                return None, 0
            expiry_date = possible_expiries[0]

            target = self.nfo_instruments[
                (self.nfo_instruments['name'] == self.flags['underlying_instrument'].split(" ")[0]) &
                (self.nfo_instruments['strike'] == atm_strike) &
                (self.nfo_instruments['instrument_type'] == option_type) &
                (
                    pd.to_datetime(
                        self.nfo_instruments['expiry'], utc=True
                    ).dt.tz_localize(None).dt.date
                    == expiry_date
                )
            ]

            if target.empty:
                logging.warning(
                    f"Could not find option for strike {atm_strike}{option_type} with expiry {expiry_date}."
                )
                return None, 0

            symbol = target.iloc[0]['tradingsymbol']
            lot_size = int(target.iloc[0]['lot_size'])
            
            margins = await asyncio.to_thread(self.kite.margins)
            capital = margins['equity']['available']['live_balance']
            if self.trading_budget:
                capital = min(capital, self.trading_budget)
            risk_amount = capital * (self.flags['risk_per_trade_percent'] / 100)
            
            option_ltp_data = await asyncio.to_thread(self.kite.ltp, f"NFO:{symbol}")
            option_price = option_ltp_data[f"NFO:{symbol}"]['last_price']
            
            if option_price <= 0:
                logging.warning(f"Option price for {symbol} is zero. Cannot calculate quantity.")
                return None, 0

            num_lots = max(1, int(risk_amount / (option_price * lot_size)))
            quantity = num_lots * lot_size

            desc = self._describe_option_symbol(symbol)
            logging.info(
                f"Trade details calculated: {desc} ({symbol}), LotSize={lot_size}, Quantity={quantity}"
            )
            return symbol, quantity
        except Exception as e:
            logging.error(f"Error in _get_trade_details: {e}", exc_info=True)
            return None, 0

    def _describe_option_symbol(self, symbol: str) -> str:
        match = self._symbol_regex.match(symbol)
        if not match:
            return symbol
        underlying, yy, m, dd, strike, opt = match.groups()
        year = 2000 + int(yy)
        month = int(m)
        day = int(dd)
        try:
            expiry = datetime.date(year, month, day).strftime('%d %b %Y')
        except ValueError:
            expiry = f"{dd}/{m}/{year}"
        return f"{underlying} {expiry} {strike} {opt}"


class PositionManagementAgent:
    """Monitors active trades and manages exits."""
    def __init__(self, kite: KiteConnect, config: dict, rag_service: RAGService):
        self.kite = kite
        self.config = config
        self.rag_service = rag_service
        self.active_trade = None
        self.cpr_pivots = {}
        self.tsl_config = self.config.get('trailing_stop_loss', {})

    async def manage(
        self,
        is_paper_trade=False,
        underlying_hist_df=None,
        sentiment_agent=None,
        openai_client=None,
        openai_lock=None,
    ):
        if not self.active_trade:
            return None
        symbol = self.active_trade['symbol']
        try:
            ltp_data = await asyncio.to_thread(self.kite.ltp, f"NFO:{symbol}")
            current_price = ltp_data[f"NFO:{symbol}"]['last_price']
        except Exception as e:
            logging.warning(f"Could not fetch LTP for managing position {symbol}: {e}")
            return "ACTIVE"

        hard_stop_loss_price = self.active_trade['initial_stop_loss']
        if current_price <= hard_stop_loss_price:
             logging.info(f"HARD stop-loss hit for {symbol} at {current_price:.2f} (SL: {hard_stop_loss_price:.2f}). Exiting.")
             return await self.exit_trade(is_paper_trade, underlying_hist_df, sentiment_agent, openai_client, openai_lock)

        self._update_premium_trailing_stop(current_price)
        trailing_sl_price = self.active_trade.get('trailing_stop_loss')
        if trailing_sl_price is not None and current_price <= trailing_sl_price:
             logging.info(f"TRAILING stop-loss hit for {symbol} at {current_price:.2f} (Trailing SL: {trailing_sl_price:.2f}). Exiting.")
             return await self.exit_trade(is_paper_trade, underlying_hist_df, sentiment_agent, openai_client, openai_lock)

        if self.tsl_config.get('use_indicator_exit') and underlying_hist_df is not None:
            if self._check_indicator_exit(underlying_hist_df):
                logging.info(f"INDICATOR-BASED exit signal triggered for {symbol}. Exiting.")
                return await self.exit_trade(is_paper_trade, underlying_hist_df, sentiment_agent, openai_client, openai_lock)

        return "ACTIVE"
    
    def _update_premium_trailing_stop(self, current_price):
        self.active_trade['high_water_mark'] = max(self.active_trade.get('high_water_mark', 0), current_price)
        trail_type = self.tsl_config.get('type', 'NONE')
        new_sl_price = self.active_trade.get('trailing_stop_loss', self.active_trade.get('initial_stop_loss', 0))
        if trail_type == 'PERCENTAGE':
            percentage = self.tsl_config.get('percentage', 15.0)
            new_sl_price = self.active_trade['high_water_mark'] * (1 - percentage / 100)
        self.active_trade['trailing_stop_loss'] = max(self.active_trade.get('trailing_stop_loss', 0), new_sl_price)

    def _check_indicator_exit(self, underlying_hist_df):
        indicator_type = self.tsl_config.get('indicator_exit_type', 'NONE')
        if underlying_hist_df.empty: return False
        underlying_price = underlying_hist_df.iloc[-1]['close']
        if indicator_type == 'MA':
            period = self.tsl_config.get('ma_period', 9)
            if f'ema_{period}' not in underlying_hist_df.columns:
                underlying_hist_df[f'ema_{period}'] = ta.ema(underlying_hist_df['close'], length=period)
            ma_value = underlying_hist_df.iloc[-1][f'ema_{period}']
            if self.active_trade['type'] == 'BUY' and underlying_price < ma_value: return True
            if self.active_trade['type'] == 'SELL' and underlying_price > ma_value: return True
        return False
    
    async def analyze_losing_trade(
        self,
        trade_details,
        underlying_df,
        sentiment_agent,
        openai_client,
        openai_lock,
    ):
        logging.info(f"Analyzing losing trade for {trade_details['Symbol']}...")
        try:
            entry_time = pd.to_datetime(
                trade_details['Timestamp'], utc=True
            ).tz_localize(None) - datetime.timedelta(minutes=10)
            exit_time = pd.to_datetime(
                trade_details['Timestamp'], utc=True
            ).tz_localize(None)
            trade_window_df = underlying_df[(underlying_df.index >= entry_time) & (underlying_df.index <= exit_time)]
            market_snapshot = trade_window_df[['open', 'high', 'low', 'close', 'volume', 'rsi']].to_string()
            news_sentiment_at_time = sentiment_agent.get_market_sentiment()
            rag_context = self.rag_service.retrieve_context_for_loss_analysis(trade_details)
            prompt = (
                "You are a trading analyst. Given the trade details, market snapshot, sentiment and context, "
                "explain why the trade lost money and suggest improvements.\n"
                f"Trade Details: {trade_details}\n"
                f"Market Snapshot: {market_snapshot}\n"
                f"News Sentiment: {news_sentiment_at_time}\n"
                f"RAG Context: {rag_context}"
            )
            backoff = 1
            while True:
                try:
                    async with openai_lock:
                        response = await openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                        )
                    break
                except Exception as e:
                    if '429' in str(e):
                        logging.warning(
                            f"OpenAI rate limit encountered during loss analysis. Retrying in {backoff} seconds."
                        )
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * 2, 60)
                    else:
                        raise
            rationale = response.choices[0].message.content.strip()
            logging.info(f"AI Rationale for Loss (with RAG): {rationale}")
            return rationale
        except Exception as e:
            logging.error(f"Failed to analyze losing trade: {e}")
            return "Analysis failed due to an internal error."

    def start_trade(self, trade_details):
        if not trade_details: return
        self.active_trade = trade_details
        self.tsl_config = self.config.get('trailing_stop_loss', {})
        stop_loss_price, _ = self._calculate_initial_sl()
        self.active_trade['initial_stop_loss'] = stop_loss_price
        self.active_trade['trailing_stop_loss'] = stop_loss_price
        self.active_trade['high_water_mark'] = self.active_trade.get('entry_price', 0)
        logging.info(f"Managing trade for {self.active_trade['symbol']}. Entry: {self.active_trade['entry_price']:.2f}, Initial Hard SL: {self.active_trade['initial_stop_loss']:.2f}")

    async def exit_trade(
        self,
        is_paper_trade=False,
        underlying_df=None,
        sentiment_agent=None,
        openai_client=None,
        openai_lock=None,
    ):
        """
        Asynchronously exits the current active trade using the isolated worker pattern.
        """
        if not self.active_trade: return None
        trade = self.active_trade
        exit_price = 0
        
        try:
            ltp_data = await asyncio.to_thread(self.kite.ltp, f"NFO:{trade['symbol']}")
            exit_price = ltp_data[f"NFO:{trade['symbol']}"]['last_price']
            
            if not is_paper_trade:
                exit_order_params = {
                    "variety": self.config['trading_flags']['order_variety'],
                    "exchange": self.kite.EXCHANGE_NFO,
                    "tradingsymbol": trade['symbol'],
                    "transaction_type": self.kite.TRANSACTION_TYPE_SELL,
                    "quantity": trade['quantity'],
                    "product": self.config['trading_flags']['product_type'],
                    "order_type": self.kite.ORDER_TYPE_MARKET,
                }
                logging.info(f"ASYNC: Preparing to place LIVE exit order -> {exit_order_params}")
                api_key = self.config['zerodha']['api_key']
                access_token = self.config['zerodha']['access_token']
                
                await asyncio.to_thread(
                    _execute_order_sync,
                    api_key,
                    access_token,
                    exit_order_params
                )
            else:
                logging.info(f"[Paper Trade] Exiting {trade['symbol']} at {exit_price:.2f}")
        except Exception as e:
            logging.error(f"Failed to execute exit for {trade['symbol']}: {e}")
        
        pnl = (exit_price - trade['entry_price']) * trade['quantity'] if exit_price > 0 else - (trade['entry_price'] * trade['quantity'])
        
        # Add OrderID to the completed trade details ---
        completed = {
            'Timestamp': datetime.datetime.now(),
            'OrderID': trade.get('order_id'), # Add the Order ID
            'Symbol': trade['symbol'], 
            'TradeType': trade['type'], 
            'EntryPrice': trade['entry_price'], 
            'ExitPrice': exit_price, 
            'Quantity': trade['quantity'], 
            'ProfitLoss': pnl, 
            'Status': 'CLOSED', 
            'Strategy': trade.get('Strategy', 'N/A')
        }
        
        if (
            pnl < 0
            and self.config['trading_flags'].get('enable_ai_loss_analysis')
            and openai_client
        ):
            rationale = await self.analyze_losing_trade(
                completed, underlying_df, sentiment_agent, openai_client, openai_lock
            )
            completed['Rationale'] = rationale
            
        self.active_trade = None
        return completed

    def _calculate_initial_sl(self):
        entry_price = self.active_trade.get('entry_price', 0)
        if entry_price == 0: return 0, 0
        sl_percent = self.config['trading_flags'].get('stop_loss_percent', 10.0)
        min_sl_points = self.config['trading_flags'].get('min_stop_loss_points', 2.0)
        percent_risk_amount = entry_price * (sl_percent / 100)
        risk_per_share = max(percent_risk_amount, min_sl_points)
        stop_loss_price = entry_price - risk_per_share
        return stop_loss_price, risk_per_share

    def _calculate_target_price(self, risk_per_share):
        entry_price = self.active_trade.get('entry_price', 0)
        if entry_price == 0: return 0
        rr_ratio = self.config['trading_flags'].get('risk_reward_ratio', 2.0)
        reward_per_share = risk_per_share * rr_ratio
        target_price = entry_price + reward_per_share
        return target_price
