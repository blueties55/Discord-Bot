import discord
from discord.ext import commands
import configparser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

# Function to read settings
def read_settings(file_path):
    config = configparser.ConfigParser()
    try:
        with open(file_path, encoding='utf-8') as f:
            config.read_file(f)
    except UnicodeDecodeError as e:
        logger.error(f"Error reading the file: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    return config['DEFAULT']

def read_dm_response(file_path):
    settings_data = read_settings(file_path)
    return settings_data.get("dm_response", "")

def read_command_prefix(file_path):
    settings_data = read_settings(file_path)
    return settings_data.get("command_prefix", "")

def read_mention_as_prefix(file_path):
    settings_data = read_settings(file_path)
    mention_as_prefix = settings_data.get("mention_as_prefix", "False")
    return mention_as_prefix.lower() == "true"

def run():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.voice_states = True

    # Read settings from settings.txt
    command_prefix = read_command_prefix('settings.txt')
    mention_as_prefix = read_mention_as_prefix('settings.txt')

    # Create the bot with the command prefix and optionally the bot mention as an alternate prefix
    if mention_as_prefix:
        bot = commands.Bot(command_prefix=commands.when_mentioned_or(command_prefix), intents=intents)
    else:
        bot = commands.Bot(command_prefix=command_prefix, intents=intents)

    @bot.event
    async def on_ready():
        # Log in as the bot
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")

        # Load the cog extensions
        extensions = [
            "cogs.role_selection",
            "cogs.auto_responses",
            "cogs.custom_commands",
            "cogs.economy",
            "cogs.economy_commands",
            "cogs.roulette",
            "cogs.tictactoe",
            "cogs.shop_commands"
        ]
        for ext in extensions:
            try:
                await bot.load_extension(ext)
                logger.info(f"{ext} extension has been loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load {ext}.py: {e}")

    @bot.event
    async def on_message(message):
        # Read DM response from settings.txt
        dm_response = read_dm_response('settings.txt')

        if message.author == bot.user:
            return

        if isinstance(message.channel, discord.DMChannel):
            if dm_response:
                reaction = "👋"
                await message.add_reaction(reaction)
                await message.author.send(dm_response)
            else:
                logger.warning("'dm_response' is empty in settings.txt. No response sent.")
        else:
            await bot.process_commands(message)

    @bot.event
    async def on_command_error(ctx, error):
        # Commented out logging as requested
        pass

    # Run the bot with the token from settings.txt
    DISCORD_API_TOKEN = read_settings('settings.txt').get("DISCORD_API_TOKEN", "")
    bot.run(DISCORD_API_TOKEN)

if __name__ == "__main__":
    run()