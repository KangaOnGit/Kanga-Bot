import discord
import os
from discord.ext import commands

# Retrieve the Discord bot token and OpenAI API key from environment variables.
discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Verify that the environment variables have been set correctly.
if not discord_bot_token or not openai_api_key:
    raise ValueError("Environment variables for tokens are not set correctly.")

# Print the first few characters of the tokens for debugging purposes.
print(f"Discord Bot Token: {discord_bot_token[:5]}...")
print(f"OpenAI API Key: {openai_api_key[:5]}...")

# Configure the bot's intents to allow it to read messages and manage voice states.

intents = discord.Intents.default()
intents.messages = True  # Enable message-related events
intents.message_content = True  # Allow reading message content
intents.guilds = True  # Enable guild-related events
intents.voice_states = True  # Enable voice state updates
intents.reactions = True

# Initialize the bot with a command prefix and the specified intents.
bot = commands.Bot(command_prefix="-", intents=intents)
bot.remove_command("help")
