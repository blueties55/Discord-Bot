import discord
from discord.ext import commands
import random
import asyncio
import sqlite3
import configparser

class Roulette(commands.Cog):
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

        # Load allowed channel ID
        self.allowed_channel_id = int(config.get('DEFAULT', 'allowed_channel_id'))

    @commands.command(name='roulette', aliases=['rl'])
    async def roulette(self, ctx, bet: int, member: discord.Member=None):
        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return
        
        if member is None:
            member = ctx.author
        user_id = member.id
        
        user_id = member.id
        self.cursor.execute("SELECT coins FROM economy WHERE user_id=?", (user_id,))
        user_coins = self.cursor.fetchone()
        
        if user_coins is None or bet <= 0:
            await ctx.send("You don't have enough coins or the bet amount is invalid.")
            return
        user_coins = user_coins[0]
        if bet > user_coins:
            await ctx.send("You don't have enough coins.")
            return

        result = str(random.randint(0, 9))  # Generating a random number between 0 and 9
        color = 'red' if int(result) % 2 != 0 else 'black'

        embed = discord.Embed(title="Roulette", description=f"Choose a color to win {2 * bet} coins!", color=discord.Colour.red())
        embed.add_field(name=f"React with :red_circle: to bet red (odd numbers)\nReact with :black_circle: to bet black (even numbers)", value=" ", inline=False)
        embed.add_field(name=f"React with number :zero: - :nine:, to win {3 * bet}!", value=" ", inline=False)
        embed.set_footer(text=f"Your current coins: {user_coins}")
        
        message = await ctx.send(embed=embed)

        await message.add_reaction('🔴') # red
        await message.add_reaction('⚫') # black
        for num in range(0, 10):
            await message.add_reaction(f'{num}\N{COMBINING ENCLOSING KEYCAP}')

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ['🔴', '⚫'] + [f'{i}\N{COMBINING ENCLOSING KEYCAP}' for i in range(10)]
        
        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("You took too long to respond.")
            return
        
        choice = str(reaction.emoji)
        if len(choice) == 1 and choice.isdigit():
            chosen_number = int(choice)
        else:
            # Extract the number from the emoji
            chosen_number = int(choice[:-1]) if choice[:-1].isdigit() else None

        if chosen_number is None:
            # Check if the user chose red or black directly
            if (choice == '⚫' and int(result) % 2 == 0) or \
               (choice == '🔴' and int(result) % 2 != 0):
                payout = bet * 2  # Payout for choosing red or black and being correct is 2 times the bet amount
                await ctx.send(f"The roulette landed on {result}. {member} won {payout} coins.")
                new_coins = user_coins + payout
            else:
                await ctx.send(f"The roulette landed on {result}. {member} lost {bet} coins.")
                new_coins = user_coins - bet
        elif chosen_number == int(result):
            payout = bet * 3  # Payout for choosing the correct number is 9 times the bet amount
            await ctx.send(f"The roulette landed on {result}. {member} won {payout} coins.")
            new_coins = user_coins + payout
        else:
            transfer_to_user_id = 1208825919356145735
            self.cursor.execute("SELECT coins FROM economy WHERE user_id = ?", (transfer_to_user_id,))
            transfer_to_coins = self.cursor.fetchone()[0]
            transfer_to_coins += bet
            self.cursor.execute("UPDATE economy SET coins=? WHERE user_id=?", (transfer_to_coins, transfer_to_user_id))
            await ctx.send(f"The roulette landed on {result}. {member} lost {bet} coins.")
            new_coins = user_coins - bet

        # Update the user's coins in the database
        self.cursor.execute("UPDATE economy SET coins=? WHERE user_id=?", (new_coins, user_id))
        self.connection.commit()

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
    await bot.add_cog(Roulette(bot))