#from src.main import API_KEY
from alpaca.trading.client import TradingClient
import os

load_dotenv()
API_KEY = os.getenv('API_KEY')
SECRET = os.getenv('SECRET')

trading_client = TradingClient(API_KEY,SECRET)

aapl_position = trading_client.get_open_position('AAPL')
