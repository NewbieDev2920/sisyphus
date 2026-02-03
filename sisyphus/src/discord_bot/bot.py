import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class SisyphusCog(discord.Cog):
    def __init__(self, bot, wallet_service, order_placer_service, register_handler):
        self.bot = bot
        self.wallet_service = wallet_service
        self.order_placer_service = order_placer_service
        self.register_handler = register_handler

    @discord.slash_command(name="hello", description="Say hello to the bot, Sisyphus will present itself and his capabilities")
    async def hello(self, ctx: discord.ApplicationContext):
        await ctx.respond("My name is Sisyphus[ALPHA V0.1], I am the eternal damned, now condemned to trade thy stocks instead of pushing boulders.")
    
    @discord.slash_command(name="subscribe", description = "Subscribe a symbol for allowing operations with the respective asset.")
    async def subscribe(self, ctx: discord.ApplicationContext, symbol : str):
        await ctx.defer()
        try:
            response = await asyncio.to_thread(self.register_handler.register_symbol,symbol.upper())
            await ctx.respond(f"Symbol ({symbol}) registered")
        except Exception as e:
            await ctx.respond(f"An error ocurred while registering : {e}")

    @discord.slash_command(name = "unsubscribe", description = "Unsubscribe a symbol will make unable operations with the respective asset..")
    async def unsubscribe(self, ctx: discord.ApplicationContext, symbol : str):
        await ctx.defer()
        try:
            response = await asyncio.to_thread(self.register_handler.unregister_symbol, symbol.upper())
            await ctx.respond(f"Symbol ({symbol} unregistered)")
        except Exception as e:
            await ctx.respond(f"An error ocurred while unregistering :{e}")

    @discord.slash_command(name="wallet", description="Show Alpaca wallet summary")
    async def wallet(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        summary = self.wallet_service.get_summary()
        await ctx.respond(f"```{summary}```")

    @discord.slash_command(name = "buy_qty", description = "Place buy order to Alpaca with asset quantity")
    async def buy_qty(self, ctx : discord.ApplicationContext, symbol : str , qty: float):
        await ctx.defer()
        try:
            response = await asyncio.to_thread(self.order_placer_service.buy_qty,symbol.upper(),qty)
            await ctx.respond(f"BUY ORDER SUBMITTED \nSYMBOL : {symbol}\nQTY: {qty}")
        except Exception as e:
            await ctx.respond(f"ERROR PLACING BUY ORDER: {str(e)}")

    @discord.slash_command(name = "sell_qty", description = "Place sell order to Alpaca with asset quantity")
    async def sell_qty(self, ctx: discord.ApplicationContext, symbol :str , qty : float):
        await ctx.defer()
        try:
            response = await asyncio.to_thread(self.order_placer_service.sell_qty,symbol.upper(),qty)
            await ctx.respond(f"SELL ORDER SUBMITTED \nSYMBOL : {symbol}\nQTY: {qty}")
        except Exception as e:
            await ctx.respond(f"ERROR PLACING SELL ORDER : {str(e)}")

    @discord.slash_command(name="buy", description="Place buy order to Alpaca with notional")
    async def buy(self, ctx: discord.ApplicationContext, symbol : str, notional: float):
        await ctx.defer()
        try:
            response = await asyncio.to_thread(self.order_placer_service.buy,symbol.upper(), notional)
            await ctx.respond(f"BUY ORDER SUBMITTED\nSYMBOL : {symbol}\nNOTIONAL : ${notional}")
        except Exception as e:
            await ctx.respond(f"ERROR PLACING BUY ORDER: {str(e)}")

    @discord.slash_command(name="sell", description = "Place sell order to Alpaca with notional")
    async def sell(self, ctx: discord.ApplicationContext, symbol: str, notional : float):
        await ctx.defer()
        try:
            response = await asyncio.to_thread(self.order_placer_service.sell,symbol.upper(), notional)
            await ctx.respond(f"SELL ORDER SUBMITTED\nSYMBOL : {symbol}\nNOTIONAL : ${notional}")
        except Exception as e:
            await ctx.respond(f"ERROR PLACING SELL ORDER: {str(e)}")

    @discord.slash_command(name="open_orders", description = "Display open orders")
    async def open_orders(self, ctx: discord.ApplicationContext):
        await ctx.defer()
        try:
            orders = await asyncio.to_thread(self.order_placer_service.get_open_orders)
            if not orders:
                 await ctx.respond("No open orders.")
                 return

            response_lines = []
            for order in orders:
                # determine amount (qty or notional)
                amount = f"{order.qty} Qty" if order.qty is not None else f"${order.notional} (Notional)"
                
                # Format: [Timestamp] Symbol | Side | Amount | Status
                line = f"[{order.created_at.strftime('%Y-%m-%d %H:%M')}] {order.symbol} | {order.side.upper()} | {amount} | Status: {order.status}"
                response_lines.append(line)
            
            response_text = "OPEN ORDERS:\n" + "\n".join(response_lines)
            
            # Simple truncation if still too long (though unlikely with this format)
            if len(response_text) > 1900:
                response_text = response_text[:1900] + "\n... (truncated)"

            await ctx.respond(f"```\n{response_text}\n```")
        except Exception as e:
            await ctx.respond(f"An error ocurred while fetching the Alpaca open orders: {e}")

    @discord.slash_command(name="get_quote", description = "Display last quote of an asset")
    async def get_quote(self, ctx: discord.ApplicationContext, symbol: str):
        # get_quote might be fast enough if cached, but safer to defer if it might hit API
        await ctx.defer()
        try:
            await ctx.respond(f"QUOTE\n[i]| {symbol} : {self.order_placer_service.get_quote(symbol)}")
        except Exception as e:
            await ctx.respond(f"ERROR FETCHING {symbol} QUOTE, MAKE SURE THE SYMBOL IS REGISTERED.")
    
    @discord.slash_command(name="registered_list", description = "Display registered list")
    async def registered_list(self, ctx: discord.ApplicationContext):
        try:
            # Operation is fast (in-memory string), no need to defer or use threads
            response = self.register_handler.registration_list()
            await ctx.respond(f"LIST: {response}")
        except Exception as e:
            await ctx.respond(f"An error ocurred while displaying the registered_list: {e}")

    @discord.slash_command(name = "fsm_status", description = "get the status of all fsm")
    async def fsm_status(self, ctx: discord.ApplicationContext):
        try:
            response = self.register_handler.fsm_status()
            await ctx.respond(f"[i]\n{response}")
        except Exception as e:
            await ctx.respond(f"An error occurred while displaying current fsm status: {e}")

class SisyphusBot(discord.Bot):

    def __init__(self, wallet_service, order_placer_service ,register_handler,debug_guilds=None):
        intents = discord.Intents.default()
        super().__init__(intents=intents, debug_guilds=debug_guilds)
        self.wallet_service = wallet_service
        self.add_cog(SisyphusCog(self, wallet_service, order_placer_service, register_handler))

    async def on_ready(self):
        print(f"[x]|{self.user} is ready and online!")
        print(f"[i]|Connected to {len(self.guilds)} guilds.")
        
        if self.debug_guilds:
            print(f"[i]|Debugging enabled for guilds: {self.debug_guilds}")
        
        # Explicitly sync commands
        print("[i] Syncing commands...")
        await self.sync_commands()
        
        # List registered commands
        print("[i] Registered Commands:")
        for cmd in self.commands:
            print(f" - /{cmd.name} (Guild IDs: {cmd.guild_ids})")
        if not self.commands:
             print("[!] WARNING: No commands registered! Check Cog loading.")


def startSisyphus(wallet_service, order_placer_service, register_handler):
    print("[x] <--- SISYPHUS IS READY TO SERVE --->")
    guild_id = os.getenv('GUILD_ID')
    
    debug_guilds = None
    if guild_id:
        try:
            debug_guilds = [int(guild_id)]
            print(f"[!] Debugging in Guild ID: {guild_id}")
        except ValueError:
            print(f"[ERROR] GUILD_ID '{guild_id}' is not a valid integer. Ignoring.")
            
    bot = SisyphusBot(wallet_service,order_placer_service, register_handler,debug_guilds=debug_guilds)
    bot.run(os.getenv("BOT_TOKEN"))
