import discord
import asyncio

class SisyphusCog(discord.Cog):
    @discord.slash_command(name="hello")
    async def hello(self, ctx):
        pass

class SisyphusBot(discord.Bot):
    def __init__(self, debug_guilds=None):
        super().__init__(intents=discord.Intents.default(), debug_guilds=debug_guilds)
        self.add_cog(SisyphusCog(self))

bot1 = discord.Bot()
bot2 = SisyphusBot(debug_guilds=[1458507060793704531])

print("Commands in bot2:", len(bot2.commands))
print("Pending in bot2:", len(bot2.pending_application_commands))
