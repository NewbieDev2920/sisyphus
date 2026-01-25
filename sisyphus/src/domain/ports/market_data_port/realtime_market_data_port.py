from abc import ABC
from abc import abstractmethod

class RealtimeMarketDataPort(ABC):

    @abstractmethod
    def get_last_quotes(symbol):
        pass


    
