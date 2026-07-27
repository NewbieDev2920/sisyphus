from infrastructure.broker.alpaca_connection import SisyphusClient
from infrastructure.account.alpaca_account import AlpacaAccount
from infrastructure.order.order_placer import OrderPlacer
from infrastructure.SisyphusExe import SisyphusExe
from infrastructure.RegisterHandler import RegisterHandler
from infrastructure.market_data.RealtimeMarketData import RealtimeMarketData
from infrastructure.console_handler import ConsoleHandler
from application.account_wallet_service import AccountWalletService
from application.order_placer_service import OrderPlacerService
from domain.strategies.basic.manual import Manual
from domain.ports.fsm.trading_fsm import TradingFSM

from discord_bot.bot import startSisyphus
import discord
import os
from dotenv import load_dotenv
import json

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
WEBSOCKET_URL = os.getenv('WEBSOCKET_URL_TEST') #cambiar entre test y real (fakepaca xor symbol)
FSM_NOTIFICATIONS_WEBHOOK =os.getenv('FSM_NOTIFICATIONS_WEBHOOK')

#GLOBAL VARIABLES
registered_symbols = {}
registered_fsm = []

config = None
with open("config.json","r", encoding="utf-8") as f:
    config = json.load(f)
fsm_configs = config.get("fsm_configs", {})
registered_symbols_list = list(fsm_configs.keys())


trading_client = SisyphusClient(API_KEY, SECRET, ENDPOINT)
alpaca_account = AlpacaAccount(trading_client)
wallet_service = AccountWalletService(alpaca_account)
order_placer_infra = OrderPlacer(trading_client)
executor = SisyphusExe(order_placer_infra)
order_placer_service = OrderPlacerService(order_placer_infra, real_time_market_data=None)

# Initialize RegisterHandler
register_handler = RegisterHandler("config.json", order_placer_service, alpaca_account, executor, fsm_configs, registered_fsm)

# Initialize market data connection with ConsoleHandler (moved up so we can use it in observers)
conn = RealtimeMarketData(WEBSOCKET_URL, API_KEY, SECRET, console_handler)
order_placer_service.real_time_market_data = conn

# REGISTER STRATEGIES FROM CONFIG
for symbol in registered_symbols_list:
    console_handler.print_bot(f"[+] Restoring FSM and strategies for {symbol}")
    fsm = TradingFSM(symbol, alpaca_account, bot_bp=10000.0, executor=executor, destiny_channel=FSM_NOTIFICATIONS_WEBHOOK)
    registered_fsm.append(fsm)
    if symbol not in register_handler.active_feeders:
        register_handler.active_feeders[symbol] = {}
        
    strategies = fsm_configs.get(symbol, [])
    for strat in strategies:
        try:
            # We call instance_strategy directly to set up feeder and memory.
            register_handler.instance_strategy(symbol, strat["name"], strat["interval_seconds"], strat.get("params", {}))
            console_handler.print_bot(f"  -> Restored {strat['name']} for {symbol}")
        except Exception as e:
            console_handler.print_bot(f"  -> Failed to restore {strat['name']}: {e}")

conn.connect()


# Wait for authentication before subscribing
console_handler.print_bot("[i] Waiting for Alpaca authentication...")
conn.authenticated_event.wait(timeout=10)

# Subscribe to registered symbols
for symbol in registered_symbols_list:
    conn.subscribe(symbol)

console_handler.print_bot("[i] Starting Discord bot...")
console_handler.print_bot("[i] Use /toggle command to switch between bot logs and stream logs")
console_handler.print_bot(f"[i] Sisyphus is using the following endpoint: {ENDPOINT}")
console_handler.print_bot(f"[i] Sisyphus is listening the following websocket : {WEBSOCKET_URL}")

# Start the bot with console_handler
startSisyphus(wallet_service, order_placer_service, register_handler, console_handler)
