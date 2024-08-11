# This code is untested. When there is time to test this program then it could be added to prod.
# import discord
# from discord.ext import commands
# import random
# import asyncio
# import sqlite3

# class Blackjack(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         self.connection = sqlite3.connect("economy.db")
#         self.cursor = self.connection.cursor()
#         self.connection.commit()
    
#     allowed_channel_ids = [1205434646087860274]

#     @commands.command(name='blackjack', aliases=['bj'])
#     async def blackjack(self, ctx, bet: int, member: discord.Member=None):
#         if ctx.channel.id not in self.allowed_channel_ids:
#             await ctx.send("Please use <#1205434646087860274> for that command")
#             return
        
#         if member is None:
#             member = ctx.author
#         user_id = member.id
        
#         self.cursor.execute("SELECT coins FROM economy WHERE user_id=?", (user_id,))
#         user_coins = self.cursor.fetchone()
        
#         if user_coins is None or bet <= 0:
#             await ctx.send("You don't have enough coins or the bet amount is invalid.")
#             return
#         user_coins = user_coins[0]
#         if bet > user_coins:
#             await ctx.send("You don't have enough coins.")
#             return

#         player_hand = [self.draw_card(), self.draw_card()]
#         dealer_hand = [self.draw_card(), self.draw_card()]
        
#         player_total = self.calculate_hand_value(player_hand)
#         dealer_total = self.calculate_hand_value(dealer_hand)
        
#         player_msg = f"Your hand: {player_hand}. Total value: {player_total}"
#         dealer_msg = f"Dealer's hand: {dealer_hand[0]}, [?]"

#         embed = discord.Embed(title="Blackjack", description=f"{player_msg}\n{dealer_msg}", color=discord.Colour.blue())
#         embed.add_field(name="Options", value="React with ✅ to stand\nReact with ⛔ to hit", inline=False)
#         embed.set_footer(text=f"Your current coins: {user_coins}")
        
#         message = await ctx.send(embed=embed)

#         await message.add_reaction('✅')  # Stand
#         await message.add_reaction('⛔')  # Hit
        
#         def check(reaction, user):
#             return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ['✅', '⛔']
        
#         while True:
#             try:
#                 reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
#             except asyncio.TimeoutError:
#                 await ctx.send("You took too long to respond.")
#                 return
            
#             if str(reaction.emoji) == '✅':  # Stand
#                 break
#             elif str(reaction.emoji) == '⛔':  # Hit
#                 player_hand.append(self.draw_card())
#                 player_total = self.calculate_hand_value(player_hand)
#                 player_msg = f"Your hand: {player_hand}. Total value: {player_total}"
#                 embed = discord.Embed(title="Blackjack", description=f"{player_msg}\n{dealer_msg}", color=discord.Colour.blue())
#                 embed.add_field(name="Options", value="React with ✅ to stand\nReact with ⛔ to hit", inline=False)
#                 embed.set_footer(text=f"Your current coins: {user_coins}")
#                 await message.edit(embed=embed)

#                 if player_total > 21:
#                     await ctx.send(f"Busted! Your hand value exceeded 21. You lost {bet} coins.")
#                     new_coins = user_coins - bet
#                     self.update_coins(user_id, new_coins)
#                     return
        
#         while dealer_total < 17:
#             dealer_hand.append(self.draw_card())
#             dealer_total = self.calculate_hand_value(dealer_hand)
        
#         dealer_msg = f"Dealer's hand: {dealer_hand}. Total value: {dealer_total}"
#         embed = discord.Embed(title="Blackjack", description=f"{player_msg}\n{dealer_msg}", color=discord.Colour.blue())
#         embed.set_footer(text=f"Your current coins: {user_coins}")

#         if dealer_total > 21 or player_total > dealer_total:
#             if len(player_hand) == 2 and player_total == 21:  # Blackjack
#                 payout = bet * 3
#                 await ctx.send(f"Congratulations! You got a Blackjack and won {payout} coins.")
#             else:
#                 payout = bet * 2
#                 await ctx.send(f"Congratulations! You won {payout} coins.")
#             new_coins = user_coins + payout
#         elif player_total == dealer_total:
#             await ctx.send("It's a tie! Your bet has been returned.")
#             new_coins = user_coins
#         else:
#             await ctx.send(f"Sorry, you lost {bet} coins.")
#             new_coins = user_coins - bet
        
#         self.update_coins(user_id, new_coins)

#     def draw_card(self):
#         """Draws a random card from the deck."""
#         card_value = random.choice(["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"])
#         return card_value

#     def calculate_hand_value(self, hand):
#         """Calculates the total value of the hand."""
#         total = 0
#         num_aces = 0
#         for card in hand:
#             if card in ["J", "Q", "K"]:
#                 total += 10
#             elif card == "A":
#                 num_aces += 1
#                 total += 11  # Start by counting ace as 11
#             else:
#                 total += int(card)  # Convert numerical cards to their integer values

#         # Adjust ace values if necessary to avoid busting
#         while total > 21 and num_aces:
#             total -= 10  # Change ace value from 11 to 1
#             num_aces -= 1

#         return total

#     def update_coins(self, user_id, coins):
#         self.cursor.execute("UPDATE economy SET coins=? WHERE user_id=?", (coins, user_id))
#         self.connection.commit()

#     def get_user_bal(self, user_id):
#         self.cursor.execute('''
#             SELECT coins FROM economy WHERE user_id = ?
#         ''', (user_id,))
#         result = self.cursor.fetchone()
#         return result[0] if result else 0
    
#     async def get_username(self, user_id):
#         user = await self.bot.fetch_user(user_id)
#         return user.display_name if user else f"Unknown User({user_id})"

# async def setup(bot):
#     await bot.add_cog(Blackjack(bot))
