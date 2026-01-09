from abc import ABC

class MarketDataPort(ABC):

    @abstractmethod
    def get_asset_price(symbol):
        pass