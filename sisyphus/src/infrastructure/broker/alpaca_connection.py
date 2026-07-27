# pyrefly: ignore [missing-import]
from alpaca.trading.client import TradingClient

def SisyphusClient(API_KEY, SECRET, ENDPOINT=None):
    if ENDPOINT:
        return TradingClient(API_KEY, SECRET,url_override=ENDPOINT)

    