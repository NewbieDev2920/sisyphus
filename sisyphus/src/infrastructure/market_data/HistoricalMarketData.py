from domain.ports.market_data_port.historical_market_data_port import HistoricalMarketDataPort
import yfinance as yf
import pandas as pd

class HistoricalMarketData(HistoricalMarketDataPort):

    #CURRENT API IMPLEMENTATION: YAHOO FINANCE API
    #RATE LIMITS https://help.yahooinc.com/dsp-api/docs/rate-limits
    #RATE LIMITES RETRIEVED 2026/01/24:
    #GET REQUESTS PER MINUTE 60
    #PUT REQUESTS PER MINUTE 30
    #POST REQUESTS PER MINUTE 30

    def __init__(self):
        pass

    #format for start and end: 'YYYY-MM-DD'

    """
    period format:
    “1d”, “5d”, “1mo”, “3mo”, “6mo”, “1y”, “2y”, “5y”, “10y”, “ytd”, “max”
    """

    """
    interval format:
    “1m”, “2m”, “5m”, “15m”, “30m”, “60m”, “90m”, “1h”, “1d”, “5d”, “1wk”, “1mo”, “3mo”
    """
    

    def get_symbol_time_series(self, symbol, period, interval, start, end) -> pandas.DataFrame:
        asset = yf.Ticker(symbol)
        return asset.history(period=period, interval=interval, start=start, end=end)

    #Symbols must be a list of strings
    def get_multiple_symbols_time_series(self, symbols, period, interval, start, end) -> pandas.DataFrame:
        string_construction = " ".join(symbols)
        assets = yf.Tickers(string_construction)
        return assets.history(period=period, interval=interval, start=start, end=end)

    def price_to_earning_ratio(self, symbol) -> float:
        asset = yf.Ticker(symbol)
        return asset.info['trailingPE']

    def dividends(self, symbol) -> float:
        asset = yf.Ticker(symbol)
        return asset.info['dividend']