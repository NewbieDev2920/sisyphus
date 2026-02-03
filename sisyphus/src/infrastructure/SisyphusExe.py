from domain.ports.fsm.sisyphus_exe_port import SisyphusExePort
from domain.ports.order_port import OrderPort

class SisyphusExe(SisyphusExePort):

    def __init__(self, order_placer : OrderPort):
        self.order_placer = order_placer
        self.open_orders = []

    def buy_notional(self, symbol, notional):
        response = self.order_placer.buy(symbol,notional)

    def sell_notional(self, symbol, notional):
        response = self.order_placer.sell(symbol,notional)

    def buy_qty(self, symbol, qty):
        response = self.order_placer.buy_qty(symbol, qty)
    
    def sell_qty(self, symbol, qty):
        response = self.order_placer.sell_qty(symbol,qty)

    def open_orders(self):
        return self.order_placer.get_open_orders()