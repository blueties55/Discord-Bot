import discord
from discord.ext import commands
import random
import asyncio
import sqlite3
import configparser

class EconomyCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connection = sqlite3.connect("economy.db")
        self.cursor = self.connection.cursor()
        self.connection.commit()
        self.allowed_channel_id = ""
        self.load_settings()

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read('settings.txt', encoding='utf-8')

        # Load allowed channel ID as an integer
        self.allowed_channel_id = int(config.get('DEFAULT', 'allowed_channel_id'))

    @commands.command(name='coinflip', aliases=['cf'])
    async def coinflip(self, ctx, bet: int, member: discord.Member = None):

        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return

        
        user_id = ctx.author.id
        self.cursor.execute("SELECT coins FROM economy WHERE user_id=?", (user_id,))
        user_coins = self.cursor.fetchone()
        
        if user_coins is None or bet <= 0:
            await ctx.send("You don't have enough coins or the bet amount is invalid.")
            return
        
        if member is None:
            member = ctx.author
        user_id = member.id
        user_coins = user_coins[0]
        
        if bet > user_coins:
            await ctx.send("You don't have enough coins.")
            return

        embed = discord.Embed(title="Coin Flip", description=f"Choose heads or tails to bet {bet} coins!", color=discord.Color.gold())
        embed.add_field(name="React with 🟢 for heads", value=" ", inline=False)
        embed.add_field(name="React with 🔵 for tails", value=" ", inline=False)
        embed.set_footer(text=f"Your current coins: {user_coins}")

        message = await ctx.send(embed=embed)

        await message.add_reaction('🟢')  # Heads
        await message.add_reaction('🔵')  # Tails

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ['🟢', '🔵']

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return

        choice = 'heads' if str(reaction.emoji) == '🟢' else 'tails'

        # Determine the result of the coin flip
        result = random.choice(['heads', 'tails'])
        if choice == result:
            await ctx.send(f"The coin landed on {result}. {member} won {bet} coins.")
            new_coins = user_coins + bet
        else:
            await self.lost_coin(user_id, bet)
            await ctx.send(f"The coin landed on {result}. {member} lost {bet} coins.")
            new_coins = user_coins - bet
        
        # Update the user's coins in the database
        self.cursor.execute("UPDATE economy SET coins=? WHERE user_id=?", (new_coins, user_id))
        self.connection.commit()

    @commands.command(name="rps")
    async def rps(self, ctx, bet: int, member: discord.Member = None):

        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return

        
        if member is None:
            member = ctx.author
        user_id = member.id
        
        user_id = ctx.author.id
        self.cursor.execute("SELECT coins FROM economy WHERE user_id=?", (user_id,))
        user_coins = self.cursor.fetchone()
        
        if user_coins is None or bet <= 0:
            await ctx.send("You don't have enough coins or the bet amount is invalid.")
            return
        
        user_coins = user_coins[0]

        if bet > user_coins:
            await ctx.send("You don't have enough coins.")
            return

        embed = discord.Embed(title="Rock Paper Scissors", description=f"Choose rock paper or scissors to bet {bet} coins!", color=discord.Color.greyple())
        embed.add_field(name="React with 🪨 for rock", value=" ", inline=False)
        embed.add_field(name="React with 📰 for paper", value=" ", inline=False)
        embed.add_field(name="React with ✂️ for scissors", value=" ", inline=False)
        embed.set_footer(text=f"Your current coins: {user_coins}")

        message = await ctx.send(embed=embed)

        await message.add_reaction('🪨')  # rock
        await message.add_reaction('📰')  # paper
        await message.add_reaction('✂️') # scissors

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ['🪨', '📰', '✂️']
        
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return
        
        if str(reaction.emoji) == '🪨':
            choice = 'rock'
        elif str(reaction.emoji) == '📰':
            choice = 'paper'
        elif str(reaction.emoji) == '✂️':
            choice = 'scissors'
        else:
            await ctx.send("Invalid choice.")
            return


        result = random.choice(['rock', 'paper', 'scissors'])
        if choice == result:
            await ctx.send(f"The Bot chose: {result}. Its a tie!")
            new_coins = user_coins

        elif (choice == 'rock' and result == 'scissors') or \
            (choice == 'scissors' and result == 'paper') or \
            (choice == 'paper' and result == 'rock'):
            await ctx.send(f"The Bot chose: {result}. {member} won {bet} coins.")
            new_coins = user_coins + bet

        else:
            await self.lost_coin(user_id, bet)
            await ctx.send(f"The Bot chose: {result}. {member} lost {bet} coins.")
            new_coins = user_coins - bet
        
        # Update the user's coins in the database
        self.cursor.execute("UPDATE economy SET coins=? WHERE user_id=?", (new_coins, user_id))
        self.connection.commit()

    @commands.command(name="higherlower", aliases=['hl'])
    async def hl(self, ctx, bet: int, member: discord.Member = None):

        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return

        
        if member is None:
            member = ctx.author
        user_id = member.id
        
        user_id = ctx.author.id
        self.cursor.execute("SELECT coins FROM economy WHERE user_id=?", (user_id,))
        user_coins = self.cursor.fetchone()
        
        if user_coins is None or bet <= 0:
            await ctx.send("You don't have enough coins or the bet amount is invalid.")
            return
        user_coins = user_coins[0]
        if bet > user_coins:
            await ctx.send("You don't have enough coins.")
            return
        
        embed = discord.Embed(title="Higher or Lower", description=f"Decide if The Bot chose a number higher or lower than 50!", color=discord.Colour.blue())
        embed.add_field(name="React with 🟢 for higher", value=" ", inline=False)
        embed.add_field(name="React with 🔴 for lower", value=" ", inline=False)
        embed.set_footer(text=f"Your current coins: {user_coins}")
        
        message = await ctx.send(embed=embed)

        await message.add_reaction('🟢') # higher
        await message.add_reaction('🔴') # lower

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ['🟢', '🔴']
        
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return
        
        choice = 'higher' if str(reaction.emoji) == '🟢' else 'lower'

        while True:
            random_number = random.randint(1, 100)

            if (random_number > 50 and choice == 'higher') or (random_number < 50 and choice == 'lower'):
                await ctx.send(f"You guessed correctly. {member} won {bet} coins!")
                new_coins = user_coins + bet
            else:
                await self.lost_coin(user_id, bet)
                await ctx.send(f"You guessed incorrectly. {member} lost {bet} coins.")
                new_coins = user_coins - bet

            # Update the user's coins in the database
            self.cursor.execute("UPDATE economy SET coins=? WHERE user_id=?", (new_coins, user_id))
            self.connection.commit()

            # Break out of the loop after one round
            break

    def get_user_bal(self, user_id): # function for retrieving the balance of user's used in the !bal and !economy commands
        self.cursor.execute('''
            SELECT coins FROM economy WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else 0
    
    async def get_username(self, user_id): # function for retrieving the user name from the user_id that is stored in the economy.db
        user = await self.bot.fetch_user(user_id)
        return user.display_name if user else f"Unknown User({user_id})"

async def setup(bot):
    await bot.add_cog(EconomyCommands(bot))