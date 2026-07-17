import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys
import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class SisyphusCog(discord.Cog):
    def __init__(self, bot, wallet_service, order_placer_service, register_handler, console_handler):
        self.bot = bot
        self.wallet_service = wallet_service
        self.order_placer_service = order_placer_service
        self.register_handler = register_handler
        self.console_handler = console_handler
        from application.backtest_service import BacktestService
        self.backtest_service = BacktestService()

    @discord.slash_command(name="hello", description="Say hello to the bot, Sisyphus will present itself and his capabilities")
    async def hello(self, ctx: discord.ApplicationContext):
        await ctx.respond("My name is Sisyphus[ALPHA V0.2], I am the eternal damned, now condemned to trade thy stocks instead of pushing boulders.")
    
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
            await ctx.respond(f"ERROR FETCHING {symbol} QUOTE, MAKE SURE THE SYMBOL IS REGISTERED. : {e}")
    
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
 
    @discord.slash_command(name="config_maps", description="Display configuration maps of all strategies in registered FSMs")
    async def config_maps(self, ctx: discord.ApplicationContext):
        try:
            response = self.register_handler.fsm_config_maps()
            await ctx.respond(f"[i]\n{response}")
        except Exception as e:
            await ctx.respond(f"An error occurred while displaying config maps: {e}")

    @discord.slash_command(name="toggle", description="Toggle console output between bot logs and stream logs")
    async def toggle(self, ctx: discord.ApplicationContext):
        try:
            self.console_handler.toggle()
            mode = "BOT" if self.console_handler.toggle_bot else "STREAM"
            await ctx.respond(f"Console toggled to {mode} mode")
        except Exception as e:
            await ctx.respond(f"An error occurred while toggling console: {e}")
 
    @discord.slash_command(
        name="backtest", 
        description="Run a backtest for a strategy on a specific symbol and date range"
    )
    async def backtest(
        self, 
        ctx: discord.ApplicationContext, 
        strategy_name: str = discord.Option(str, description="Name of strategy (e.g. MonotonicIncreasing)", choices=["MonotonicIncreasing", "Floor", "Manual"]),
        symbol: str = discord.Option(str, description="Stock symbol (e.g. AAPL)"),
        start_date: str = discord.Option(str, description="Start Date (YYYY-MM-DD)"),
        end_date: str = discord.Option(str, description="End Date (YYYY-MM-DD)"),
        interval: str = discord.Option(str, description="Time interval (e.g. 1d, 1h, 1m)", default="1d"),
        cash: float = discord.Option(float, description="Initial cash balance", default=10000.0)
    ):
        await ctx.defer()
        try:
            # Ejecutar en hilo secundario para evitar bloquear el bot de Discord y causar timeouts/desconexiones de red
            report_path, plot_path, summary_text = await asyncio.to_thread(
                self.backtest_service.run_backtest,
                strategy_name,
                symbol.upper(),
                start_date,
                end_date,
                interval,
                cash
            )
            
            # Preparar archivos para adjuntar
            files = [discord.File(report_path)]
            if plot_path:
                files.append(discord.File(plot_path))
            
            await ctx.respond(
                content=f"📊 **Backtest Complete for {symbol.upper()} ({strategy_name})**\n```\n{summary_text}\n```",
                files=files
            )
        except Exception as e:
            await ctx.respond(f"❌ **Backtest Failed**: {str(e)}")

    @discord.slash_command(
        name="backtest_manual", 
        description="Run a manual buy-and-hold backtest on a specific symbol and date range"
    )
    async def backtest_manual(
        self, 
        ctx: discord.ApplicationContext, 
        symbol: str = discord.Option(str, description="Stock symbol (e.g. AAPL)"),
        start_date: str = discord.Option(str, description="Start Date (YYYY-MM-DD)"),
        end_date: str = discord.Option(str, description="End Date (YYYY-MM-DD)"),
        qty: float = discord.Option(float, description="Number of shares to buy", default=None),
        notional: float = discord.Option(float, description="Dollar amount to buy", default=None),
        interval: str = discord.Option(str, description="Time interval (e.g. 1d, 1h, 1m)", default="1d"),
        cash: float = discord.Option(float, description="Initial cash balance", default=10000.0)
    ):
        await ctx.defer()
        try:
            if qty is None and notional is None:
                await ctx.respond("❌ **Error**: You must specify either `qty` or `notional` to purchase.")
                return

            # Ejecutar en hilo secundario para evitar bloquear el bot de Discord y causar timeouts/desconexiones de red
            report_path, plot_path, summary_text = await asyncio.to_thread(
                self.backtest_service.run_manual_backtest,
                symbol.upper(),
                start_date,
                end_date,
                interval,
                cash,
                qty,
                notional
            )
            
            # Preparar archivos para adjuntar
            files = [discord.File(report_path)]
            if plot_path:
                files.append(discord.File(plot_path))
            
            await ctx.respond(
                content=f"📊 **Manual Backtest Complete for {symbol.upper()}**\n```\n{summary_text}\n```",
                files=files
            )
        except Exception as e:
            await ctx.respond(f"❌ **Manual Backtest Failed**: {str(e)}")

    @discord.slash_command(
        name="backtest_floor", 
        description="Run a backtest for the Floor strategy with a specific floor price"
    )
    async def backtest_floor(
        self, 
        ctx: discord.ApplicationContext, 
        symbol: str = discord.Option(str, description="Stock symbol (e.g. AAPL)"),
        start_date: str = discord.Option(str, description="Start Date (YYYY-MM-DD)"),
        end_date: str = discord.Option(str, description="End Date (YYYY-MM-DD)"),
        floor_price: float = discord.Option(float, description="Stop-loss price"),
        qty: float = discord.Option(float, description="Number of shares to buy initially", default=None),
        notional: float = discord.Option(float, description="Dollar amount to buy initially", default=None),
        interval: str = discord.Option(str, description="Time interval (e.g. 1d, 1h, 1m)", default="1d"),
        cash: float = discord.Option(float, description="Initial cash balance", default=10000.0)
    ):
        await ctx.defer()
        try:
            if qty is None and notional is None:
                await ctx.respond("❌ **Error**: You must specify either `qty` or `notional` to purchase.")
                return

            # Ejecutar en hilo secundario para evitar bloquear el bot de Discord y causar timeouts/desconexiones de red
            report_path, plot_path, summary_text = await asyncio.to_thread(
                self.backtest_service.run_floor_backtest,
                symbol.upper(),
                start_date,
                end_date,
                floor_price,
                interval,
                cash,
                qty,
                notional
            )
            
            # Preparar archivos para adjuntar
            files = [discord.File(report_path)]
            if plot_path:
                files.append(discord.File(plot_path))
            
            await ctx.respond(
                content=f"📊 **Floor Backtest Complete for {symbol.upper()}**\n```\n{summary_text}\n```",
                files=files
            )
        except Exception as e:
            await ctx.respond(f"❌ **Floor Backtest Failed**: {str(e)}")

    @discord.slash_command(
        name="backtest_downside_momentum_risk", 
        description="Run a backtest for the Downside Momentum Risk strategy"
    )
    async def backtest_downside_momentum_risk(
        self, 
        ctx: discord.ApplicationContext, 
        symbol: str = discord.Option(str, description="Stock symbol (e.g. BTC-USD)"),
        start_date: str = discord.Option(str, description="Start Date (YYYY-MM-DD)"),
        end_date: str = discord.Option(str, description="End Date (YYYY-MM-DD)"),
        short_alpha: float = discord.Option(float, description="Short term alpha (e.g. 0.1)", default=0.1),
        long_alpha: float = discord.Option(float, description="Long term alpha (e.g. 0.01)", default=0.01),
        threshold: float = discord.Option(float, description="Z-Score Threshold (e.g. 2.0)", default=2.0),
        qty: float = discord.Option(float, description="Number of shares to buy initially", default=None),
        notional: float = discord.Option(float, description="Dollar amount to buy initially", default=None),
        interval: str = discord.Option(str, description="Time interval (e.g. 1d, 1h, 1m)", default="1d"),
        cash: float = discord.Option(float, description="Initial cash balance", default=10000.0)
    ):
        await ctx.defer()
        try:
            if qty is None and notional is None:
                await ctx.respond("❌ **Error**: You must specify either `qty` or `notional` to purchase.")
                return

            report_path, plot_path, summary_text = await asyncio.to_thread(
                self.backtest_service.run_downside_momentum_risk_backtest,
                symbol.upper(),
                start_date,
                end_date,
                short_alpha,
                long_alpha,
                threshold,
                interval,
                cash,
                qty,
                notional
            )
            
            files = [discord.File(report_path)]
            if plot_path:
                files.append(discord.File(plot_path))
            
            await ctx.respond(
                content=f"📊 **Downside Momentum Risk Backtest Complete for {symbol.upper()}**\n```\n{summary_text}\n```",
                files=files
            )
        except Exception as e:
            await ctx.respond(f"❌ **Downside Momentum Risk Backtest Failed**: {str(e)}")


class SisyphusBot(discord.Bot):

    def __init__(self, wallet_service, order_placer_service ,register_handler, console_handler, debug_guilds=None):
        intents = discord.Intents.default()
        super().__init__(intents=intents, debug_guilds=debug_guilds)
        self.wallet_service = wallet_service
        self.console_handler = console_handler
        self.add_cog(SisyphusCog(self, wallet_service, order_placer_service, register_handler, console_handler))

    async def on_ready(self):
        self.console_handler.print_bot(f"[x]|{self.user} is ready and online!")
        self.console_handler.print_bot(f"[i]|Connected to {len(self.guilds)} guilds.")
        
        if self.debug_guilds:
            self.console_handler.print_bot(f"[i]|Debugging enabled for guilds: {self.debug_guilds}")
        
        # List registered commands BEFORE syncing
        self.console_handler.print_bot("[i] Registered Commands BEFORE syncing:")
        for cmd in self.commands:
            self.console_handler.print_bot(f" - /{cmd.name} (Guild IDs: {cmd.guild_ids})")
        if not self.commands:
             self.console_handler.print_bot("[!] WARNING: No commands registered!")
             
        # Explicitly sync commands
        self.console_handler.print_bot("[i] Syncing commands...")
        await self.sync_commands()
        
        # List registered commands AFTER syncing
        self.console_handler.print_bot("[i] Registered Commands AFTER syncing:")
        for cmd in self.commands:
            self.console_handler.print_bot(f" - /{cmd.name} (Guild IDs: {cmd.guild_ids})")


def startSisyphus(wallet_service, order_placer_service, register_handler, console_handler):
    msg = "[x] <--- SISYPHUS IS READY TO SERVE --->"
    console_handler.print_bot(msg)
    console_handler.star_bot_log(msg)
    
    guild_id = os.getenv('GUILD_ID')
    
    debug_guilds = None
    if guild_id:
        try:
            debug_guilds = [int(guild_id)]
            console_handler.print_bot(f"[!] Debugging in Guild ID: {guild_id}")
        except ValueError:
            console_handler.print_bot(f"[ERROR] GUILD_ID '{guild_id}' is not a valid integer. Ignoring.")
            
    bot = SisyphusBot(wallet_service, order_placer_service, register_handler, console_handler, debug_guilds=debug_guilds)
    bot.run(os.getenv("BOT_TOKEN"))
