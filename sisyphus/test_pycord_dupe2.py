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

bot = SisyphusBot(debug_guilds=[1458507060793704531])
print("Pending Commands:", len(bot.pending_application_commands))
for cmd in bot.pending_application_commands:
    print(cmd.name, cmd.guild_ids)
