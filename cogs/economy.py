import discord
from discord.ext import commands, tasks
import sqlite3
import time
import configparser

class Economy(commands.Cog): # the economy class holds all the commands for your economy most notably !addcoins, !bal, and !economy
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        self.owner_role = ""
        self.allowed_channel_id = ""
        self.load_settings()

        self.connection = sqlite3.connect("economy.db") # this block opens the economy.db file or creates it if it doesn't exist and makes all information available for the bot
        self.cursor = self.connection.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS economy (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER DEFAULT 500,
                last_voice_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily (
        user_id INTEGER PRIMARY KEY,
        last_claim INTEGER DEFAULT 0
    		)
		''')
        self.connection.commit()

        # Start the background task to update coins for users in voice chat
        self.update_bal_task.start()
    
    def load_settings(self):
        config = configparser.ConfigParser()
        config.read('settings.txt', encoding='utf-8')

        # Load owner role
        self.owner_role = config.get('DEFAULT', 'owner_role')

        # Load allowed channel ID as an integer
        self.allowed_channel_id = int(config.get('DEFAULT', 'allowed_channel_id'))


    @commands.command(name='addcoins', aliases=['ac'], hidden=True)
    async def addcoins(self,ctx, member: discord.Member, amount: int):
        # Check if user has the required role to run this command
        if not any(role.name == self.owner_role for role in ctx.author.roles):
            await ctx.send("You don't have the required role to use this command.")
            return

        """ Add coins to a users account """

        if amount <= 0:
            await ctx.send("Please provide a positive amount of coins to add.")
            return
        
        await self.add_coins(member.id, amount)

        await ctx.send(f"Successfully added {amount} coins to {member.display_name}'s account.")

    @commands.command(name='removecoins', aliases=['rc'], hidden=True)
    async def removecoins(self,ctx, member: discord.Member, amount: int):
        # Check if user has the required role to run this command
        if not any(role.name == self.owner_role for role in ctx.author.roles):
            await ctx.send("You don't have the required role to use this command.")
            return
        
        """ Removes coins from a users account """

        if amount <= 0:
            await ctx.send("Please provide a positive amount of coins to add.")
            return
        
        await self.remove_coins(member.id, amount)

        await ctx.send(f"Successfully removed {amount} coins to {member.display_name}'s account.")

    @commands.command(name='payment', aliases=['pay'])
    async def payment(self, ctx, recipient: discord.Member, amount: int):

        """ Give a user coins from your account to theirs """

        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return


        if amount <= 0:
            await ctx.send("Please provide a positive amount of coins to pay.")
            return

        payer_id = ctx.author.id
        payer_bal = self.get_user_bal(payer_id)
        if payer_bal < amount:
            await ctx.send("You do not have enough coins to make this payment.")
            return

        await self.pay_coins(payer_id, recipient.id, amount)
        await ctx.send(f"Successfully paid {recipient.display_name} {amount} coins.")

    @commands.command(name='bal') # check a users balance
    async def show_bal(self, ctx, member: discord.Member = None):

        """ Check the balance of coins for a user """

        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return

        
        if member is None:
            member = ctx.author

        user_id = member.id
        bal = self.get_user_bal(user_id)

        embed = discord.Embed(
            title=f"{member}'s current balance!",
            colour=discord.Colour.dark_magenta(),
            description=f"{member} | Coins: {bal}"
        )
        embed.set_footer(text="Please report any issues to server admin!")

        await ctx.send(embed=embed)

    @commands.command(name='economy') # gives the balance of all users in order from most to least coins
    async def economy_command(self, ctx):

        """ Check the total economy of the server """

        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return

        
        guild = ctx.guild
        economy = await self.get_economy(guild)

        top_economy = sorted(economy, key=lambda x: x[1], reverse=True)[:15]

        embed = discord.Embed(title="Server's Economy: Top 15", colour=0x480476)
        for index, (username, coins) in enumerate(top_economy, start=1):
            embed.add_field(name=f"{index}. {username}", value=f"Balance: {coins}", inline=False)
        
        embed.set_footer(text="Please report any issues to server admin!")
        await ctx.send(embed=embed)

    @tasks.loop(minutes=2) # starts the timer for 2 minutes that users are in any voice channel to give them 10 coins 
    async def update_bal_task(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.voice and member.voice.channel:
                    user_id = member.id
                    await self.add_coins(user_id, 2)
                    
    @commands.command(name='daily')
    async def daily(self, ctx):

        """Claim daily coins (500 coins every 24 hours)."""
        
        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return

        
        user_id = ctx.author.id
        last_claim_time = self.get_last_claim_time(user_id)

        if last_claim_time is not None and time.time() - last_claim_time < 24 * 60 * 60:
            await ctx.send("You've already claimed your daily coins. Please try again later.")
            return

        await self.add_coins(user_id, 500)
        await ctx.send("500 coins have been added to your account. Come back tomorrow for more!")

        self.update_last_claim_time(user_id)

    def get_last_claim_time(self, user_id):
        self.cursor.execute('''
            SELECT last_claim FROM daily WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_last_claim_time(self, user_id):
        self.cursor.execute('''
            INSERT OR REPLACE INTO daily (user_id, last_claim) VALUES (?, ?)
        ''', (user_id, int(time.time())))
        self.connection.commit()

    @commands.Cog.listener() # gives users 10 coins but they only recieve coins for each new message after 60 seconds since their last message
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        user_id = message.author.id
        if user_id in self.cooldowns and time.time() - self.cooldowns[user_id] < 60:
            return

        await self.add_coins(user_id, 2)
        self.cooldowns[user_id] = time.time()

    async def add_coins(self, user_id, amount): # adding the coins to the economy.db file
        self.cursor.execute('''
            INSERT OR IGNORE INTO economy (user_id) VALUES (?)
        ''', (user_id,))

        self.cursor.execute('''
            UPDATE economy SET coins = coins + ?, last_voice_update = CURRENT_TIMESTAMP WHERE user_id = ?
        ''', (amount, user_id))

        self.connection.commit()

    async def remove_coins(self, user_id, amount):
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO economy (user_id) VALUES (?)
            ''', (user_id,))
            
            self.cursor.execute('''
                UPDATE economy SET coins = coins - ?, last_voice_update = CURRENT_TIMESTAMP WHERE user_id = ?
            ''', (amount, user_id))

            self.connection.commit()
        except Exception as e:
            print(f"An error occurred: {e}")
            self.connection.rollback()


    async def pay_coins(self, payer_id, recipient_id, amount):
        self.cursor.execute('''
            INSERT OR IGNORE INTO economy (user_id) VALUES (?)
        ''', (payer_id,))
        
        self.cursor.execute('''
            INSERT OR IGNORE INTO economy (user_id) VALUES (?)
        ''', (recipient_id,))

        self.cursor.execute('''
            UPDATE economy SET coins = coins - ? WHERE user_id = ?
        ''', (amount, payer_id))

        self.cursor.execute('''
            UPDATE economy SET coins = coins + ? WHERE user_id = ?
        ''', (amount, recipient_id))

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
    
    async def get_economy(self, guild): # function for reading all the database info and putting it in order from most to least coins for the !economy command
        self.cursor.execute('''
            SELECT user_id, coins FROM economy ORDER BY coins DESC 
        ''')
        economy_data = self.cursor.fetchall()

        economy = []
        for user_id, coins in economy_data:
            username = await self.get_username(user_id)
            economy.append((username, coins))

        return economy
    
    def cog_unload(self): # unloads the cog, updates the balance of users, and closes the database when the cog is stopped
        self.update_bal_task.cancel()
        self.connection.close()

async def setup(bot):
    await bot.add_cog(Economy(bot))