import discord
from discord.ext import commands
import sqlite3
import random
import configparser

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.connection = sqlite3.connect("economy.db")
        self.cursor = self.connection.cursor()
        self.connection.commit()
        self.game_board = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        self.current_player = ""
        self.game_over = True
        self.player_x = None
        self.player_o = None
        self.bet = 0
        self.allowed_channel_id = ""
        self.load_settings()

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read('settings.txt', encoding='utf-8')

        # Load allowed channel ID as an integer
        self.allowed_channel_id = int(config.get('DEFAULT', 'allowed_channel_id'))

    def print_board(self):
        board = ""
        for i in range(0, 9, 3):
            board += " | ".join(self.game_board[i:i+3]) + "\n"
            if i < 6:
                board += "--------------\n"
        return board

    def check_winner(self):
        for i in range(0, 3):
            if self.game_board[i*3] == self.game_board[i*3+1] == self.game_board[i*3+2]:
                return True
            if self.game_board[i] == self.game_board[i+3] == self.game_board[i+6]:
                return True
        if self.game_board[0] == self.game_board[4] == self.game_board[8] or self.game_board[2] == self.game_board[4] == self.game_board[6]:
            return True
        return False

    @commands.command(name="tictactoe", aliases=["ttt"])
    async def start_game(self, ctx, opponent: discord.Member, bet: int):
        """!tictactoe or !ttt @user bet amount"""
        if ctx.channel.id != self.allowed_channel_id:
            await ctx.send(f"Please use <#{self.allowed_channel_id}> for that command.")
            return
        if not self.game_over:
            await ctx.send("A game is already in progress. Finish the current game before starting a new one.")
            return

        # Check if both players have enough coins
        if not self.check_balance(ctx.author.id, bet) or not self.check_balance(opponent.id, bet):
            await ctx.send("Both players must have enough coins to bet.")
            return

        # Deduct the bet amount from both players
        self.update_balance(ctx.author.id, -bet)
        self.update_balance(opponent.id, -bet)

        self.game_board = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        self.current_player = "❌"
        self.game_over = False
        self.player_x = ctx.author
        self.player_o = opponent
        self.bet = bet

        if self.current_player == "⭕":
            await ctx.send(f"{self.player_o.mention} goes first. Please wait for their move.")
        else:
            embed = discord.Embed(title="Tic-Tac-Toe", description=f"{ctx.author.mention} (❌) has challenged {opponent.mention} (⭕) to a game! ❌ goes first.\n{self.print_board()}")
            embed.set_footer(text=f"Playing for: {self.bet * 2} coins!")
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.author == self.player_x and not self.game_over and message.content.isdigit() and self.current_player == "❌":
            move = int(message.content) - 1
            if 0 <= move < 9 and self.game_board[move] != "❌" and self.game_board[move] != "⭕":
                self.game_board[move] = self.current_player
                embed = discord.Embed(title="Tic-Tac-Toe", description=f"Current player: {self.current_player}\n{self.print_board()}")
                embed.set_footer(text=f"Playing for: {self.bet * 2} coins!")
                await message.channel.send(embed=embed)
                if self.check_winner():
                    await message.channel.send(f"{self.current_player} wins!")
                    self.game_over = True
                elif all(cell == "❌" or cell == "⭕" for cell in self.game_board):
                    await message.channel.send("It's a tie!")
                    self.update_balance(self.player_x.id, self.bet)
                    self.update_balance(self.player_o.id, self.bet)
                    self.game_over = True
                else:
                    self.current_player = "⭕"
                    await message.channel.send(f"It's {self.player_o.mention}'s turn.")

        elif message.author == self.player_o and not self.game_over and message.content.isdigit() and self.current_player == "⭕":
            move = int(message.content) - 1
            if 0 <= move < 9 and self.game_board[move] != "❌" and self.game_board[move] != "⭕":
                self.game_board[move] = self.current_player
                embed = discord.Embed(title="Tic-Tac-Toe", description=f"Current player: {self.current_player}\n{self.print_board()}")
                embed.set_footer(text=f"Playing for: {self.bet * 2} coins!")
                await message.channel.send(embed=embed)
                if self.check_winner():
                    await message.channel.send(f"{self.current_player} wins {self.bet * 2} coins!")
                    self.update_balance(self.player_o.id, self.bet * 2)
                    self.game_over = True
                elif all(cell == "❌" or cell == "⭕" for cell in self.game_board):
                    await message.channel.send("It's a tie! Both players have received their bets back.")
                    self.update_balance(self.player_x.id, self.bet)
                    self.update_balance(self.player_o.id, self.bet)
                    self.game_over = True
                else:
                    self.current_player = "❌"
                    await message.channel.send(f"It's {self.player_x.mention}'s turn.")

    @commands.command(name="endttt")
    async def end_game(self, ctx):
        """ !endttt will end the current tictactoe game and refund all bets"""
        if not self.game_over:
            self.update_balance(self.player_x.id, self.bet)
            self.update_balance(self.player_o.id, self.bet)
            await ctx.send("The game has been ended. Both players have received their bets back.")
            self.game_over = True
        else:
            await ctx.send("There is no active game to end.")

    def update_balance(self, user_id, amount):
        self.cursor.execute("UPDATE economy SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
        self.connection.commit()

    def check_balance(self, user_id, bet):
        self.cursor.execute("SELECT coins FROM economy WHERE user_id = ?", (user_id,))
        coins = self.cursor.fetchone()[0]
        return coins >= bet

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))
