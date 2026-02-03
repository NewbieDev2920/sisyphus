from abc import ABC
from abc import abstractmethod

class OrderPort(ABC):

    @abstractmethod
    def asset_status() -> str:
        pass
    
    @abstractmethod
    def buy():
        pass

    @abstractmethod
    def sell():
        pass

    @abstractmethod
    def buy_qty():
        pass

    @abstractmethod
    def sell_qty():
        pass