from abc import ABC
from abc import abstractmethod

class HistoricalMarketDataPort(ABC):
    
    @abstractmethod
    def get_symbol_time_series(symbol, period, interval, start, end) -> pandas.DataFrame:
        pass

    #Symbols must be a list of strings
    @abstractmethod
    def get_multiple_symbols_time_series(symbols, period, interval, start, end) -> pandas.DataFrame:
        pass

    @abstractmethod
    def price_to_earning_ratio(symbol) -> float:
        pass

    @abstractmethod
    def dividends(symbol) -> float:
        pass


    
