import os
import pandas as pd
from domain.ports.market_data_port.historical_market_data_port import HistoricalMarketDataPort
from infrastructure.market_data.HistoricalMarketData import HistoricalMarketData
from infrastructure.console_handler import get_console_handler

class CachedHistoricalMarketData(HistoricalMarketDataPort):
    def __init__(self, cache_dir="data/historical"):
        self.raw_provider = HistoricalMarketData()
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_filename(self, symbol, period, interval, start, end):
        # Limpiar caracteres conflictivos
        start_str = start if start else "none"
        end_str = end if end else "none"
        period_str = period if period else "none"
        filename = f"cache_{symbol}_{period_str}_{interval}_{start_str}_{end_str}.csv"
        return os.path.join(self.cache_dir, filename)

    def get_symbol_time_series(self, symbol, period, interval, start, end) -> pd.DataFrame:
        cache_path = self._get_cache_filename(symbol, period, interval, start, end)
        
        if os.path.exists(cache_path):
            get_console_handler().print_bot(f"[i] Loading historical data for {symbol} from cache: {cache_path}")
            # Leer CSV, parseando la fecha como índice
            df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
            return df
        
        get_console_handler().print_bot(f"[i] Cache miss. Downloading historical data for {symbol} via yfinance...")
        df = self.raw_provider.get_symbol_time_series(symbol, period, interval, start, end)
        
        if df is not None and not df.empty:
            df.to_csv(cache_path)
            get_console_handler().print_bot(f"[+] Saved historical data for {symbol} to cache: {cache_path}")
        
        return df

    def get_multiple_symbols_time_series(self, symbols, period, interval, start, end) -> pd.DataFrame:
        # Para múltiples símbolos, descargamos uno por uno y los unimos
        dfs = {}
        for symbol in symbols:
            df = self.get_symbol_time_series(symbol, period, interval, start, end)
            if df is not None and not df.empty:
                dfs[symbol] = df
        
        if not dfs:
            return pd.DataFrame()
            
        return pd.concat(dfs, axis=1)

    def price_to_earning_ratio(self, symbol) -> float:
        return self.raw_provider.price_to_earning_ratio(symbol)

    def dividends(self, symbol) -> float:
        return self.raw_provider.dividends(symbol)
