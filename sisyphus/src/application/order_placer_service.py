from domain.ports.order_port import OrderPort
from domain.strategies.base import Base

class OrderPlacerService:
    #CAMBIAR ORDER_PLACER POR MANUAL STRATEGY.
    def __init__(self, order_placer : OrderPort, real_time_market_data):
        self.order_placer = order_placer
        self.manual_strategies = {}
        self.real_time_market_data = real_time_market_data

    def subscribe_manual(self, manual_strategy : Base):
        self.manual_strategies[manual_strategy.symbol] = manual_strategy

    def unsubscribe_manual(self, symbol):
        try:
            del self.manual_strategies[symbol]
        except Exception as e:
            print(f"Error : {e}")

    def buy(self, symbol, notional):
        try:
            self.manual_strategies[symbol].buy_notional(notional)
        except Exception as e:
            self.manual_strategy_error(e)
    
    def sell(self, symbol, notional):
        try:
            self.manual_strategies[symbol].sell_notional(notional)
        except Exception as e:
            self.manual_strategy_error(e)

    def buy_qty(self, symbol, qty):
        try:
            self.manual_strategies[symbol].buy(qty)
        except Exception as e:
            self.manual_strategy_error(e)

    def sell_qty(self, symbol, qty):
        try:
            self.manual_strategies[symbol].sell(qty)
        except Exception as e:
            self.manual_strategy_error(e)

    def get_open_orders(self):
        return self.order_placer.get_open_orders()

    def manual_strategy_error(self, e : Exception):
        print(f"There is no manual strategy for this symbol : {e}")

    def get_quote(self,symbol):
        return self.real_time_market_data.symbol_to_quote[symbol]
    
