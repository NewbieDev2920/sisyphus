from domain.ports.order_port import OrderPort

class OrderPlacerService:
    def __init__(self, order_placer : OrderPort):
        self.order_placer = order_placer

    def buy(self, symbol, notional):
        self.order_placer.buy(symbol,notional)
    
    def sell(self, symbol, notional):
        self.order_placer.buy(symbol,notional)

    def get_open_orders(self):
        self.order_placer.get_open_orders()
    
