from abc import ABC, abstractmethod
from infrastructure.order.order_placer import OrderPlacer

class SisyphusExePort(ABC):

    def __init__(self, order_placer : OrderPlacer):
        self.order_placer = order_placer