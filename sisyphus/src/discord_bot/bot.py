import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class SisyphusCog(discord.Cog):
    def __init__(self, bot, wallet_service, order_placer_service):
        self.bot = bot
        self.wallet_service = wallet_service
        self.order_placer_service = order_placer_service

    @discord.slash_command(name="hello", description="Say hello to the bot, Sisyphus will present itself and his capabilities")
    async def hello(self, ctx: discord.ApplicationContext):
        await ctx.respond("My name is Sisyphus[ALPHA V0.1], I am the eternal damned, now condemned to trade thy stocks instead of pushing boulders.")
    
    @discord.slash_command(name="wallet", description="Show Alpaca wallet summary")
    async def wallet(self, ctx: discord.ApplicationContext):
        summary = self.wallet_service.get_summary()
        await ctx.respond(f"```{summary}```")

    @discord.slash_command(name="buy", description="Place buy order to Alpaca")
    async def buy(self, ctx: discord.ApplicationContext, symbol : str, notional: float):
        try:
            response = await asyncio.to_thread(self.order_placer_service.buy,symbol.upper(), notional)
            await ctx.respond(f"BUY ORDER SUBMITTED\nSYMBOL : {symbol}\nNOTIONAL : ${notional}")
        except Exception as e:
            await ctx.respond(f"ERROR PLACING BUY ORDER: {str(e)}")

    @discord.slash_command(name="sell", description = "Place sell order to Alpaca")
    async def sell(self, ctx: discord.ApplicationContext, symbol: str, notional : float):
        try:
            response = await asyncio.to_thread(self.order_placer_service.sell,symbol.upper(), notional)
            await ctx.respond(f"SELL ORDER SUBMITTED\nSYMBOL : {symbol}\nNOTIONAL : ${notional}")
        except Exception as e:
            await ctx.respond(f"ERROR PLACING SELL ORDER: {str(e)}")

    @discord.slash_command(name="open_orders", description = "Display open orders")
    async def open_orders(self, ctx: discord.ApplicationContext):
        try:
            response = self.order_placer_service.get_open_orders()
            await ctx.respond(f"[i]| OPEN_ORDERS: \n{str(response)}")
        except Exception as e:
            await ctx.respond("An error ocurred while fetching the Alpaca open orders.")      

class SisyphusBot(discord.Bot):

    def __init__(self, wallet_service, order_placer_service ,debug_guilds=None):
        intents = discord.Intents.default()
        super().__init__(intents=intents, debug_guilds=debug_guilds)
        self.wallet_service = wallet_service
        self.add_cog(SisyphusCog(self, wallet_service, order_placer_service))

    async def on_ready(self):
        print(f"[x] {self.user} is ready and online!")
        print(f"[i] Connected to {len(self.guilds)} guilds.")
        
        if self.debug_guilds:
            print(f"[i] Debugging enabled for guilds: {self.debug_guilds}")
        
        # Explicitly sync commands
        print("[i] Syncing commands...")
        await self.sync_commands()
        
        # List registered commands
        print("[i] Registered Commands:")
        for cmd in self.commands:
            print(f" - /{cmd.name} (Guild IDs: {cmd.guild_ids})")
        if not self.commands:
             print("[!] WARNING: No commands registered! Check Cog loading.")


def startSisyphus(wallet_service, order_placer_service):
    print("[x] <--- SISYPHUS IS READY TO SERVE --->")
    guild_id = os.getenv('GUILD_ID')
    
    debug_guilds = None
    if guild_id:
        try:
            debug_guilds = [int(guild_id)]
            print(f"[!] Debugging in Guild ID: {guild_id}")
        except ValueError:
            print(f"[ERROR] GUILD_ID '{guild_id}' is not a valid integer. Ignoring.")
            
    bot = SisyphusBot(wallet_service,order_placer_service, debug_guilds=debug_guilds)
    bot.run(os.getenv("BOT_TOKEN"))
