from domain.ports.fsm.states import State
from domain.signals import Signal
from domain.events.event import Event
from domain.events.fsm import StateChange, OrderResolved
from domain.events.market import PriceUpdate
from domain.events.strategy import SignalEvent


class TradingFSM:

    def __init__(
        self,
        symbol: str,
        alpaca_account,
        bot_bp: float,
        executor,
        current_state=State.FLAT,
        limit: int = 3
    ):
        self.executor = executor
        self.symbol = symbol
        self.bot_bp = bot_bp
        self.alpaca_account = alpaca_account

        self.current_state = current_state
        self.limit = limit

        self.is_active = True
        self.strategies = []

        self.offer_price: float | None = None

        # Sync initial state
        self._sync_state_from_position()

        # ================================
        # Dispatchers
        # ================================

        self._event_handlers = {
            SignalEvent: self._handle_signal_event,
            StateChange: self._handle_state_change,
            OrderResolved: self._handle_order_resolved,
            PriceUpdate: self._handle_price_update,
        }

        self._signal_handlers = {
            Signal.BUY: self._handle_buy,
            Signal.SELL: self._handle_sell,
            Signal.BUY_NOTIONAL: self._handle_buy_notional,
            Signal.SELL_NOTIONAL: self._handle_sell_notional,
        }

    # =====================================================
    # EVENT ROUTER
    # =====================================================

    def on_event(self, event: Event):

        handler = self._event_handlers.get(type(event))

        if not handler:
            print(f"No handler for {type(event)}")
            return

        handler(event)

    # =====================================================
    # EVENT HANDLERS
    # =====================================================

    def _handle_signal_event(self, event: SignalEvent):

        self._dispatch_signal(
            event.signal,
            event.numeric_value
        )

    def _handle_state_change(self, event: StateChange):

        self.current_state = event.new_state

    def _handle_order_resolved(self, event: OrderResolved):

        # Cuando una orden se llena → recalcular estado
        self._sync_state_from_position()

    def _handle_price_update(self, event: PriceUpdate):

        self.offer_price = float(event.price)

    # =====================================================
    # SIGNAL ROUTER
    # =====================================================

    def _dispatch_signal(self, signal: Signal, value):

        handler = self._signal_handlers.get(signal)

        if not handler:
            print(f"No handler for {signal}")
            return

        handler(value)

    # =====================================================
    # SIGNAL HANDLERS
    # =====================================================

    # -------- BUY (QTY) --------

    def _handle_buy(self, qty: float):

        if qty <= 0:
            return

        cash = self._get_cash()
        price = self.symbol_approx_price()

        cost = qty * price

        if cash < cost:
            print(f"Insufficient funds: {cash} < {cost}")
            return

        self._buy_qty(qty)

    # -------- SELL (QTY) --------

    def _handle_sell(self, qty: float):

        if qty <= 0:
            return

        pos_qty = self.asset_qty()

        if pos_qty < qty:
            print("Not enough assets to sell")
            return

        self._sell_qty(qty)

    # -------- BUY (NOTIONAL) --------

    def _handle_buy_notional(self, amount: float):

        if amount <= 0:
            return

        cash = self._get_cash()

        if cash < amount:
            print("Insufficient funds")
            return

        self._buy_notional(amount)

    # -------- SELL (NOTIONAL) --------

    def _handle_sell_notional(self, amount: float):

        pos_value = self.asset_qty() * self.symbol_approx_price()

        if pos_value < amount:
            print("Not enough position value")
            return

        self._sell_notional(amount)

    # =====================================================
    # EXECUTION LAYER
    # =====================================================

    def _buy_qty(self, qty: float):

        print(f"BUY {qty} {self.symbol}")

        self.executor.buy_qty(self.symbol,qty)

    def _sell_qty(self, qty: float):

        print(f"SELL {qty} {self.symbol}")

        self.executor.sell_qty(self.symbol,qty)

    def _buy_notional(self, amount: float):

        print(f"BUY {self.symbol} for ${amount}")

        self.executor.buy_notional(self.symbol,amount)

    def _sell_notional(self, amount: float):

        print(f"SELL {self.symbol} for ${amount}")

        self.executor.sell_notional(self.symbol, amount)

    # =====================================================
    # STATE MANAGEMENT
    # =====================================================

    def _sync_state_from_position(self):

        qty = self.asset_qty()

        if qty >= self.limit:
            self.current_state = State.LONG
        else:
            self.current_state = State.FLAT

    # =====================================================
    # HELPERS
    # =====================================================

    def _get_cash(self) -> float:

        return float(self.alpaca_account.cash)

    def asset_qty(self) -> float:

        # Debe consultar Alpaca
        # pos = self.alpaca_account.get_position(self.symbol)
        # return float(pos.qty)

        return 0.0

    def symbol_approx_price(self) -> float:

        if self.offer_price is None:
            raise Exception("Price not available")

        return self.offer_price

    def validate_strategies(self):

        for s in self.strategies:

            if s.symbol != self.symbol:
                raise Exception("INCOMPATIBLE STRATEGY SYMBOL")

    def set_limit(self, new_limit: int):

        self.limit = new_limit
