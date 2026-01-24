from abc import ABC
from abc import abstractmethod

class RealtimeMarketDataPort(ABC):

    @abstractmethod
    def get_asset_price(symbol):
        pass

    @abstractmethod
    def get_asset_volume(symbol):
        pass

    
