from infrastructure.broker.alpaca_connection import SisyphusClient
from infrastructure.account.alpaca_account import AlpacaAccount
from infrastructure.order.order_placer import OrderPlacer
from infrastructure.SisyphusExe import SisyphusExe
from infrastructure.RegisterHandler import RegisterHandler
from infrastructure.market_data.RealtimeMarketData import RealtimeMarketData
from infrastructure.console_handler import ConsoleHandler
from application.account_wallet_service import AccountWalletService
from application.order_placer_service import OrderPlacerService
from domain.strategies.manual import Manual
from domain.ports.fsm.trading_fsm import TradingFSM

from discord_bot.bot import startSisyphus
import discord
import os
from dotenv import load_dotenv
import json


# SIMPLIFIED APPROACH: Don't wrap bot in Terminal User Interface to avoid event loop conflicts
# The bot will run normally, TUI is only for market data display

# Initialize ConsoleHandler early (before any prints)
from infrastructure.console_handler import ConsoleHandler, set_console_handler
console_handler = ConsoleHandler(toggle_bot=True)
set_console_handler(console_handler)  # Make it globally accessible

console_handler.print_bot("[O] Initializing Sisyphus ...")

#.ENV VARIABLES
load_dotenv() # load all the variables from the env file
bot = discord.Bot()
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')
SECRET = os.getenv('SECRET')
ENDPOINT = os.getenv('ENDPOINT')
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL')

#GLOBAL VARIABLES
registered_symbols = None
registered_fsm = []

config = None
with open("config.json","r", encoding="utf-8") as f:
    config = json.load(f)
registered_symbols = config["registered_symbols"]


trading_client = SisyphusClient(API_KEY,SECRET)
alpaca_account = AlpacaAccount(trading_client)
wallet_service = AccountWalletService(alpaca_account)
order_placer_infra = OrderPlacer(trading_client)
executor = SisyphusExe(order_placer_infra)
order_placer_service = OrderPlacerService(order_placer_infra, real_time_market_data=None)
register_handler = RegisterHandler("config.json",order_placer_service,alpaca_account,executor, registered_symbols, registered_fsm)

# REGISTER STRATEGIES
for symbol in registered_symbols:
    console_handler.print_bot(f"[+] Registering manual strategy for {symbol}")
    fsm = TradingFSM(symbol, alpaca_account, bot_bp=10000.0, executor=executor)
    registered_fsm.append(fsm)
    strategy = Manual(symbol, fsm)
    fsm.strategies.append(strategy)
    order_placer_service.subscribe_manual(strategy)

# Remove duplicate console_handler initialization (moved to top)
# Initialize market data connection with ConsoleHandler
conn = RealtimeMarketData(WEBSOCKET_URL, API_KEY, SECRET, console_handler)
conn.connect()
#REFACTORIZAR ESTO.
order_placer_service.real_time_market_data = conn

# Wait for authentication before subscribing
console_handler.print_bot("[i] Waiting for Alpaca authentication...")
conn.authenticated_event.wait(timeout=10)

# Subscribe to registered symbols
for symbol in registered_symbols:
    conn.subscribe(symbol)

console_handler.print_bot("[i] Starting Discord bot...")
console_handler.print_bot("[i] Use /toggle command to switch between bot logs and stream logs")

# Start the bot with console_handler
startSisyphus(wallet_service, order_placer_service, register_handler, console_handler)
