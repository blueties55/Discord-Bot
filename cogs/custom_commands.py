import discord
from discord.ext import commands

class Customcommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Simple commands and the template for any new commands
    @commands.command(name='ping')
    async def ping_command(self, ctx):
        await ctx.send('pong')
    
    # Add the Autoresponses cog to the bot
async def setup(bot):
    await bot.add_cog(Customcommands(bot))