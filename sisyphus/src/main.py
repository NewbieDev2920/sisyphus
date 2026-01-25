from infrastructure.broker.alpaca_connection import SisyphusClient
from infrastructure.account.alpaca_account import AlpacaAccount
from infrastructure.order.order_placer import OrderPlacer
from application.account_wallet_service import AccountWalletService
from discord_bot.bot import startSisyphus
import discord
import os 
from dotenv import load_dotenv

print("[O] Initialiazing Sisyphus ...")

load_dotenv() # load all the variables from the env file
bot = discord.Bot()

BOT_TOKEN = os.getenv('BOT_TOKEN')
API_KEY = os.getenv('API_KEY')
SECRET = os.getenv('SECRET')
ENDPOINT = os.getenv('ENDPOINT')

trading_client = SisyphusClient(API_KEY,SECRET)
alpaca_account = AlpacaAccount(trading_client)
wallet_service = AccountWalletService(alpaca_account)
order_placer = OrderPlacer(trading_client)
startSisyphus(wallet_service, order_placer)



