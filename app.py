import Settings
print("Settings loaded")

import Background_Checker  # If it contains bot tasks or commands
print("Background Checker loaded")

import Bot_Guide           # If it contains bot tasks or commands
print("Bot Guide loaded")

import Music_Commands      # If it contains bot tasks or commands
print("Music loaded")

import Nim_Game_Commands   # If it contains bot tasks or commands
print("Nim Game loaded")

import Generic_Game_Commands  # Ensure this file registers commands
print("Generic Game loaded")

import Generic_Game_Shop   # If it contains bot tasks or commands
print("Generic Game Shop loaded")

from Settings import bot, discord_bot_token

if __name__ == "__main__":
    bot.run(discord_bot_token)
