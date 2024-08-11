import discord
from discord.ext import commands
import configparser
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

class Autoresponses(commands.Cog):
    def __init__(self, bot, dm_response, keyword_responses, filter_terms):
        self.bot = bot
        self.dm_response = dm_response
        self.keyword_responses = keyword_responses
        self.filter_terms = filter_terms

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from the bot itself to avoid infinite loops
        if message.author == self.bot.user:
            return

        # Check for keywords in the message content
        for keyword_data in self.keyword_responses:
            keyword = keyword_data.get("keyword", "").lower()
            if keyword in message.content.lower():
                # Add default reaction
                default_reaction = "👀"
                await message.add_reaction(default_reaction)

                # Respond with predefined responses
                responses = keyword_data.get("response", [""])
                for response in responses:
                    await message.channel.send(response)

                return  # Stop checking other keywords after handling one

        # Check and delete messages matching filter terms
        for term_data in self.filter_terms:
            term = term_data.get("term", "").lower()
            if term in message.content.lower():
                # Delete the message
                await message.delete()

                # Respond with predefined response
                responses = term_data.get("response", [""])
                if responses:
                    for response in responses:
                        await message.channel.send(response)

                return  # Stop checking other terms after handling one

        # Check if someone mentions the bot in a message using the @bot
        if self.bot.user.mentioned_in(message):
            await self.on_mention(message)

    async def on_mention(self, message):
        """Handle mentions of the bot."""
        if isinstance(message.channel, discord.DMChannel):
            # Respond with DM response
            await message.channel.send(self.dm_response)
        else:
            # Handle mention in a server channel
            reactions = ["👋"]  # Default reaction on mention

            # Add reactions
            for reaction in reactions:
                await message.add_reaction(reaction)

            # Respond with predefined responses
            await message.channel.send(self.dm_response)

async def setup(bot):
    config = configparser.ConfigParser()

    # Read settings with UTF-8 encoding from the updated file
    try:
        with open('auto_responses_settings.txt', encoding='utf-8') as f:
            config.read_file(f)
    except UnicodeDecodeError as e:
        logger.error(f"Error reading settings file: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"Settings file not found: {e}")
        raise

    # Read DM response
    dm_response = config['DEFAULT'].get('dm_response', 'Hi! How can I help you?')

    # Read keyword responses
    keyword_responses = []
    i = 1
    while f'keyword_{i}' in config['DEFAULT']:
        keyword = config['DEFAULT'].get(f'keyword_{i}', '')
        response = config['DEFAULT'].get(f'response_{i}', '')
        keyword_responses.append({
            'keyword': keyword,
            'response': response.split('\n')  # Handle multiple responses
        })
        i += 1

    # Read filter terms
    filter_terms = []
    j = 1
    while f'filter_{j}' in config['DEFAULT']:
        term = config['DEFAULT'].get(f'filter_{j}', '')
        response = config['DEFAULT'].get(f'response_filter_{j}', '')
        filter_terms.append({
            'term': term,
            'response': response.split('\n')  # Handle multiple responses
        })
        j += 1

    # Set up the cog
    await bot.add_cog(Autoresponses(bot, dm_response, keyword_responses, filter_terms))