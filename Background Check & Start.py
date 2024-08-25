@bot.event
async def on_command_error(ctx, error):
    # Event triggered when an error occurs during the execution of a command.
    if isinstance(error, commands.CommandNotFound):
        # Send a message if the command is not found.
        await ctx.send("Command not found. Please use a valid command.")
        print("Command not found.")
    else:
        # Send a message with the error details.
        await ctx.send(f"An error occurred: {error}")
        print(f"An error occurred: {error}")


@bot.command()
async def hello(ctx):
    # Command to send a greeting message including the sender's name and ID.
    print("Received hello command")
    await ctx.send(f"Hello {ctx.author} ({ctx.author.id})!")


@bot.command()
async def ping(ctx):
    # Command to check the bot's latency and send it as a message.
    print("Received ping command")
    # Convert latency from seconds to milliseconds.
    latency = bot.latency * 1000
    await ctx.send(f"Kanga's Bot's Ping is {latency:.2f} ms")


@bot.event
async def on_message(message):
    # Event triggered when a message is received.
    print(f"Message from {message.author} in {
          message.channel}: {message.content}")
    if message.author == bot.user:
        return
    await bot.process_commands(message)  # Process commands in the message.

# Start the bot with the specified token.
bot.run(discord_bot_token)
