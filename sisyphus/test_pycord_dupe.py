import discord
import asyncio

class TestCog(discord.Cog):
    @discord.slash_command(name="ping")
    async def ping(self, ctx):
        pass

class TestBot(discord.Bot):
    def __init__(self):
        super().__init__()
        self.add_cog(TestCog(self))
        try:
            self.add_cog(TestCog(self))
        except Exception as e:
            print("Exception when adding cog twice:", type(e).__name__, e)

bot = TestBot()
print("Commands after init:", len(bot.commands))
