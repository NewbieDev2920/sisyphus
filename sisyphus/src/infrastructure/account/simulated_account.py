from domain.ports.account_port import AccountPort

class SimulatedAccount(AccountPort):
    def __init__(self, initial_cash: float = 10000.0):
        self._cash = initial_cash
        self._positions = {}  # {symbol: quantity}
        self._current_prices = {}  # {symbol: price} (updated step by step in backtest)

    def set_current_price(self, symbol: str, price: float):
        self._current_prices[symbol] = price

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def equity(self) -> float:
        return self._cash + self.long_market_value

    @property
    def pending_transfer(self) -> dict:
        return {"pending_transfer_in": 0.0, "pending_transfer_out": 0.0}

    @property
    def long_market_value(self) -> float:
        value = 0.0
        for symbol, qty in self._positions.items():
            price = self._current_prices.get(symbol, 0.0)
            value += qty * price
        return value

    def summary(self) -> str:
        positions_str = ", ".join([f"{sym}: {qty:.4f}" for sym, qty in self._positions.items()])
        return (
            f"--- SIMULATED ACCOUNT ---\n"
            f"Cash: ${self._cash:.2f}\n"
            f"Market Value: ${self.long_market_value:.2f}\n"
            f"Equity: ${self.equity:.2f}\n"
            f"Positions: [{positions_str if positions_str else 'None'}]"
        )

    def get_position_qty(self, symbol: str) -> float:
        return float(self._positions.get(symbol, 0.0))

    def get_position_value(self, symbol: str) -> float:
        qty = self.get_position_qty(symbol)
        price = self._current_prices.get(symbol, 0.0)
        return qty * price

    def update_balance(self, cash_diff: float, symbol: str, qty_diff: float):
        self._cash += cash_diff
        self._positions[symbol] = self._positions.get(symbol, 0.0) + qty_diff
        # Si la posición se reduce a cero (o menor por imprecisiones flotantes), eliminarla
        if self._positions[symbol] <= 1e-8:
            self._positions.pop(symbol, None)
