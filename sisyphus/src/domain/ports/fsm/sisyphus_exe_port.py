from abc import ABC, abstractmethod
from infrastructure.order.order_placer import OrderPlacer

class SisyphusExePort(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def buy_qty(self, symbol, qty):
        pass

    @abstractmethod
    def sell_qty(self, symbol, qty):
        pass

    @abstractmethod
    def buy_notional(self, symbol, notional):
        pass

    @abstractmethod
    def sell_notional(self, symbol, notional):
        pass

