import discord
from discord.ext import commands
import configparser

class RoleSelection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reaction_message_id = None
        self.default_roles = []
        self.role_data = {}
        self.owner_role = ""
        self.load_settings()

    def load_settings(self):
        config = configparser.ConfigParser()
        config.read('role_selection_settings.txt', encoding='utf-8')

        # Load owner role
        self.owner_role = config.get('DEFAULT', 'owner_role', fallback='')

        # Load default roles
        default_roles_str = config.get('DEFAULT', 'new_user_roles', fallback='')
        self.default_roles = [role.strip() for role in default_roles_str.split(',')]

        # Load role selection data
        self.role_data = {}
        for key in config['DEFAULT']:
            if key.startswith('role_selection_'):
                index = key.split('_')[2]
                emoji = config.get('DEFAULT', f'role_selection_{index}_emoji', fallback='').strip()
                name = config.get('DEFAULT', f'role_selection_{index}_name', fallback='').strip()
                role_name = config.get('DEFAULT', f'role_selection_{index}_role_name', fallback='').strip()
                if emoji and name and role_name:
                    self.role_data[emoji] = {"name": name, "role_name": role_name}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        for role_name in self.default_roles:
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                await member.add_roles(role)

    @commands.command()
    async def roleselection(self, ctx):
        # Check if user has the required role to run this command
        if not any(role.name == self.owner_role for role in ctx.author.roles):
            await ctx.send("You don't have the required role to use this command.")
            return

        embed = discord.Embed(title="Role Shop", description="React to get a role!", color=discord.Color.blurple())
        for emoji, item_data in self.role_data.items():
            embed.add_field(name=f"{item_data['name']}", value=f"{emoji}", inline=True)

        message = await ctx.send(embed=embed)
        self.reaction_message_id = message.id  # Set reaction_message_id
        for emoji in self.role_data.keys():
            await message.add_reaction(emoji)

        def check(reaction, user):
            return user != self.bot.user and reaction.message.id == message.id and str(reaction.emoji) in self.role_data

        while True:
            reaction, user = await self.bot.wait_for('reaction_add', check=check)

            item_data = self.role_data.get(str(reaction.emoji))
            if not item_data:
                await ctx.send("Invalid choice!")
                continue
            
            role_name = item_data["role_name"]
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if role:
                await user.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id == self.reaction_message_id:
            guild = self.bot.get_guild(payload.guild_id)
            if guild:
                member = guild.get_member(payload.user_id)
                if member:
                    emoji = payload.emoji.name if payload.emoji.is_custom_emoji() else str(payload.emoji)
                    role_name = self.role_data.get(emoji, {}).get('role_name')
                    if role_name:
                        role = discord.utils.get(guild.roles, name=role_name)
                        if role:
                            await member.remove_roles(role)

async def setup(bot):
    await bot.add_cog(RoleSelection(bot))