from domain.ports.fsm.sisyphus_exe_port import SisyphusExePort
from domain.events.fsm import OrderResolved
from infrastructure.console_handler import get_console_handler

class SimulatedExecutor(SisyphusExePort):
    def __init__(self, account, slippage_pct: float = 0.0, commission: float = 0.0):
        super().__init__()
        self.account = account
        self.slippage_pct = slippage_pct
        self.commission = commission
        self.current_prices = {}  # {symbol: price}
        self.fsm_list = []  # FSMs to notify
        self.trade_events = []  # Log of executed trades

    def register_fsm(self, fsm):
        self.fsm_list.append(fsm)

    def set_current_price(self, symbol: str, price: float):
        self.current_prices[symbol] = price

    def _get_price(self, symbol: str) -> float:
        if symbol not in self.current_prices:
            raise ValueError(f"Price for {symbol} is not available in simulation.")
        return self.current_prices[symbol]

    def _notify_fsms(self, order_id, symbol, numeric_value, side):
        # Crear evento OrderResolved para que el FSM actualice su estado
        event = OrderResolved(order_id, symbol, numeric_value, side)
        for fsm in self.fsm_list:
            if fsm.symbol == symbol:
                fsm.on_event(event)

    def buy_qty(self, symbol, qty):
        price = self._get_price(symbol)
        # Deslizamiento de precio al alza en compras
        exec_price = price * (1.0 + self.slippage_pct)
        cost = qty * exec_price
        total_cost = cost + self.commission

        if self.account.cash < total_cost:
            get_console_handler().print_bot(
                f"[SimulatedExecutor] BUY REJECTED: Insufficient Cash. Needed ${total_cost:.2f}, had ${self.account.cash:.2f}"
            )
            return

        # Actualizar cuenta
        self.account.update_balance(-total_cost, symbol, qty)
        trade_id = f"sim_buy_qty_{len(self.trade_events) + 1}"
        
        self.trade_events.append({
            "id": trade_id,
            "symbol": symbol,
            "side": "BUY",
            "qty": qty,
            "price": exec_price,
            "total_value": cost,
            "total_cost": total_cost,
            "cash_after": self.account.cash
        })
        
        self._notify_fsms(trade_id, symbol, qty, "BUY")

    def sell_qty(self, symbol, qty):
        current_qty = self.account.get_position_qty(symbol)
        if current_qty < qty:
            # Vender solo lo que se posee
            qty = current_qty

        if qty <= 0.0:
            return

        price = self._get_price(symbol)
        # Deslizamiento a la baja en ventas
        exec_price = price * (1.0 - self.slippage_pct)
        revenue = qty * exec_price
        total_revenue = revenue - self.commission

        # Actualizar cuenta
        self.account.update_balance(total_revenue, symbol, -qty)
        trade_id = f"sim_sell_qty_{len(self.trade_events) + 1}"
        
        self.trade_events.append({
            "id": trade_id,
            "symbol": symbol,
            "side": "SELL",
            "qty": qty,
            "price": exec_price,
            "total_value": revenue,
            "total_cost": -total_revenue,
            "cash_after": self.account.cash
        })
        
        self._notify_fsms(trade_id, symbol, qty, "SELL")

    def buy_notional(self, symbol, notional):
        price = self._get_price(symbol)
        exec_price = price * (1.0 + self.slippage_pct)
        qty = notional / exec_price
        self.buy_qty(symbol, qty)

    def sell_notional(self, symbol, notional):
        price = self._get_price(symbol)
        exec_price = price * (1.0 - self.slippage_pct)
        qty = notional / exec_price
        self.sell_qty(symbol, qty)
