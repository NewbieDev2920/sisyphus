import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

class TestCog(discord.Cog):
    @discord.slash_command(name="ping")
    async def ping(self, ctx):
        await ctx.respond("Pong!")

class TestBot(discord.Bot):
    def __init__(self, debug_guilds=None):
        super().__init__(intents=discord.Intents.default(), debug_guilds=debug_guilds)
        self.add_cog(TestCog(self))
    
    async def on_ready(self):
        print("Commands BEFORE manual sync:", len(self.commands))
        await self.sync_commands()
        print("Commands AFTER manual sync:", len(self.commands))
        await self.close()

bot = TestBot(debug_guilds=[int(os.getenv('GUILD_ID'))])
bot.run(os.getenv("BOT_TOKEN"))
