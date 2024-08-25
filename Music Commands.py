# Dictionaries to manage voice clients, song queues, and played songs.
queues = {}  # Dictionary to store song queues for each guild
voice_clients = {}  # Dictionary to store voice clients for each guild
played_songs = {}  # Dictionary to keep track of played songs
currently_playing = {}  # Dictionary to keep track of the currently playing song

# Base URL and options for YouTube video extraction.
youtube_base_url = 'https://www.youtube.com/'
youtube_results_url = youtube_base_url + 'results?'
youtube_watch_url = youtube_base_url + 'watch?v='
yt_dl_options = {"format": "bestaudio/best"}
# Create an instance of YoutubeDL with options
ytdl = ytdlp.YoutubeDL(yt_dl_options)
ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                  'options': '-vn -filter:a "volume=0.25"'}


@bot.command()
async def play(ctx, *, link):
    # Command to play a YouTube video in the user's voice channel.
    try:
        # Get the voice channel of the user who invoked the command.
        voice_channel = ctx.author.voice.channel
        if not voice_channel:
            await ctx.send("You need to be in a voice channel to play music.")
            print("User not in a voice channel.")
            return

        # Connect to the voice channel if not already connected.
        if ctx.guild.id in voice_clients:
            voice_client = voice_clients[ctx.guild.id]
        else:
            print(f"Attempting to join {voice_channel}...")
            voice_client = await voice_channel.connect()
            voice_clients[ctx.guild.id] = voice_client
            print(f"Joined {voice_channel}")

        # If the link is not a YouTube URL, search for it.
        if youtube_base_url not in link:
            # Search for keywords and encode it
            query_string = urllib.parse.urlencode({'search_query': link})
            content = urllib.request.urlopen(
                youtube_results_url + query_string)  # Open the link
            search_results = re.findall(
                r'/watch\?v=(.{11})', content.read().decode())

            if not search_results:
                await ctx.send("No search results found.")
                print("No search results found.")
                return

            link = youtube_watch_url + search_results[0]  # Return ful link

        # Extract information from the YouTube link using yt-dlp.
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(link, download=False))

        song_url = data['url']
        song_title = data.get('title', 'Unknown Title')
        player = discord.FFmpegPCMAudio(song_url, **ffmpeg_options)

        # Initialize the queue if not already done.
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        if ctx.guild.id not in played_songs:
            played_songs[ctx.guild.id] = set()

        # Add the song to the queue if the bot is already playing.
        if voice_client.is_playing() or ctx.guild.id in currently_playing:
            # Add song url and title as tuple
            queues[ctx.guild.id].append((song_url, song_title))
            await ctx.send("Added to the queue.")
            print("Added to the queue.")
        else:
            # Start playing the song if nothing is currently playing.
            currently_playing[ctx.guild.id] = (song_url, song_title)
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                play_next(ctx), bot.loop))
            await ctx.send(f"Now playing: {song_title}")
            print(f"Now playing: {song_title}")
            played_songs[ctx.guild.id].add(song_url)

    except Exception as e:
        # Send an error message if something goes wrong.
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")


@bot.command()
async def play_next(ctx):
    # Function to play the next song in the queue.
    try:
        if ctx.guild.id in queues and queues[ctx.guild.id]:
            next_song_url, next_song_title = queues[ctx.guild.id].pop(0)
            currently_playing[ctx.guild.id] = (next_song_url, next_song_title)
            voice_client = voice_clients.get(ctx.guild.id)
            if voice_client:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(next_song_url, download=False))
                song_url = data['url']
                player = discord.FFmpegPCMAudio(song_url, **ffmpeg_options)
                voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                    play_next(ctx), bot.loop))
                await ctx.send(f"Now playing: {next_song_title}")
                print(f"Now playing: {next_song_title}")
                played_songs[ctx.guild.id].add(next_song_url)
        else:
            currently_playing.pop(ctx.guild.id, None)
            print(f"Queue is empty for guild: {ctx.guild.id}")
    except Exception as e:
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")


@bot.command()
async def resume(ctx):
    # Command to resume the paused audio.
    print("Received resume command")
    try:
        user_voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice_clients.get(ctx.guild.id)

    # Ensure the user is in the same voice channel as the bot
        if user_voice_channel is None:
            await ctx.send("You are not in a voice channel.")
            print(f"User {ctx.author.id} is not in a voice channel.")
            return
        if bot_voice_channel is None:
            await ctx.send("Bot is not connected to a voice channel.")
            print(f"Bot is not connected to a voice channel.")
            return

        if user_voice_channel != bot_voice_channel:
            await ctx.send("You must be in the same voice channel as the bot to perform this action.")
            print(
                f"User {ctx.author.id} is not in the same voice channel as the bot.")
            return

        if ctx.guild.id in voice_clients and voice_clients[ctx.guild.id].is_paused():
            voice_clients[ctx.guild.id].resume()
            await ctx.send("Playback resumed.")
            print("Playback resumed.")
        else:
            await ctx.send("No audio is currently paused.")
            print("No audio is currently paused.")
    except Exception as e:
        # Send an error message if something goes wrong.
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")


@bot.command()
async def stop(ctx):
    # Command to stop the currently playing audio.
    try:
        user_voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice_clients.get(ctx.guild.id)

    # Ensure the user is in the same voice channel as the bot
        if user_voice_channel is None:
            await ctx.send("You are not in a voice channel.")
            print(f"User {ctx.author.id} is not in a voice channel.")
            return
        if bot_voice_channel is None:
            await ctx.send("Bot is not connected to a voice channel.")
            print(f"Bot is not connected to a voice channel.")
            return

        if user_voice_channel != bot_voice_channel:
            await ctx.send("You must be in the same voice channel as the bot to perform this action.")
            print(
                f"User {ctx.author.id} is not in the same voice channel as the bot.")
            return

        if ctx.guild.id in voice_clients and voice_clients[ctx.guild.id].is_playing():
            voice_clients[ctx.guild.id].stop()
            await ctx.send("Playback stopped.")
            print("Playback stopped.")
        else:
            await ctx.send("No audio is currently playing.")
            print("No audio is currently playing.")
    except Exception as e:
        # Send an error message if something goes wrong.
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")


@bot.command()
async def queue(ctx, *, url):
    # Command to add a song URL to the queue.
    try:
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []
        queues[ctx.guild.id].append(url)
        # Update played_songs to allow re-adding of previously played songs
        if ctx.guild.id not in played_songs:
            played_songs[ctx.guild.id] = set()
        if url in played_songs[ctx.guild.id]:
            # Remove song that has been played
            played_songs[ctx.guild.id].remove(url)
        await ctx.send("Added to queue!")
    except Exception as e:
        # Send an error message if something goes wrong.
        print(f"Error: {e}")
        await ctx.send(f"Error: {e}")


@bot.command(name="clear_queue")
async def clear_queue(ctx):
    # Command to clear the song queue.
    try:
        user_voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice_clients.get(ctx.guild.id)

    # Ensure the user is in the same voice channel as the bot
        if user_voice_channel is None:
            await ctx.send("You are not in a voice channel.")
            print(f"User {ctx.author.id} is not in a voice channel.")
            return
        if bot_voice_channel is None:
            await ctx.send("Bot is not connected to a voice channel.")
            print(f"Bot is not connected to a voice channel.")
            return

        if user_voice_channel != bot_voice_channel:
            await ctx.send("You must be in the same voice channel as the bot to perform this action.")
            print(
                f"User {ctx.author.id} is not in the same voice channel as the bot.")
            return

        if ctx.guild.id in queues:
            queues[ctx.guild.id].clear()
            await ctx.send("Queue has been cleared.")
            print("Queue cleared.")
        else:
            await ctx.send("No songs in queue to be cleared.")
    except Exception as e:
        # Send an error message if something goes wrong.
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")


@bot.command(name="skip")
async def skip(ctx):
    # Command to skip the current track and play the next one in the queue.
    try:
        user_voice_channel = ctx.author.voice.channel
        bot_voice_channel = voice_clients.get(ctx.guild.id)

    # Ensure the user is in the same voice channel as the bot
        if user_voice_channel is None:
            await ctx.send("You are not in a voice channel.")
            print(f"User {ctx.author.id} is not in a voice channel.")
            return
        if bot_voice_channel is None:
            await ctx.send("Bot is not connected to a voice channel.")
            print(f"Bot is not connected to a voice channel.")
            return

        if user_voice_channel != bot_voice_channel:
            await ctx.send("You must be in the same voice channel as the bot to perform this action.")
            print(
                f"User {ctx.author.id} is not in the same voice channel as the bot.")
            return

        if ctx.guild.id in voice_clients and voice_clients[ctx.guild.id].is_playing():
            voice_clients[ctx.guild.id].stop()
            await play_next(ctx)
            await ctx.send("Skipped current track!")
            print("Skipped current track")
        else:
            await ctx.send("No songs in queue to skip track.")
            print("No songs in queue to be able to skip.")
    except Exception as e:
        # Send an error message if something goes wrong.
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")


@bot.command(name="queue_list")
async def queue_list(ctx):
    # Command to display the list of songs currently in the queue.
    guild_id = ctx.guild.id

    try:
        currently_playing_message = ""
        if guild_id in currently_playing:
            song_url, song_title = currently_playing[guild_id]
            currently_playing_message = f"{
                song_title} (Currently Playing)\n"

        # Retrieve the list of songs in the queue
        if guild_id in queues and queues[guild_id]:
            queue_message = ""
            for i, (song_url, song_title) in enumerate(queues[guild_id], start=1):
                queue_message += f"{i}. {song_title}\n"
            await ctx.send(currently_playing_message + queue_message)
        else:
            await ctx.send(currently_playing_message + "The queue is currently empty.")
    except Exception as e:
        # Send an error message if something goes wrong.
        print(f"Error: {e}")
        await ctx.send(f"Error: {e}")


@tasks.loop(seconds=300)  # Periodically check every 30 seconds.
async def check_voice_channels():
    # Periodically check voice channels to disconnect if only the bot is present.
    for guild_id, voice_client in voice_clients.items():
        if voice_client.is_connected():
            channel = voice_client.channel
            # Only the bot is left in the channel.
            if len(channel.members) == 1:
                await voice_client.disconnect()
                if guild_id in queues:
                    queues[guild_id] = []
                print(f"Disconnected from {channel} as it was empty.")


@bot.command(name="del_song")
async def del_song(ctx, position: int):

    # Ensure the guild has a queue
    if ctx.guild.id not in queues:
        await ctx.send("Queue does not exist for this guild.")
        print("Queue does not exist for this guild.")
        return

    # Ensure the position is within the valid range
    if not (1 <= position <= len(queues[ctx.guild.id])):
        await ctx.send("Invalid position. Please provide a valid position.")
        print(f"Invalid position: {position}")
        return

    # Get the voice channel of the user and the bot
    user_voice_channel = ctx.author.voice.channel
    bot_voice_channel = voice_clients.get(ctx.guild.id)

    # Ensure the user is in the same voice channel as the bot
    if user_voice_channel is None:
        await ctx.send("You are not in a voice channel.")
        print(f"User {ctx.author.id} is not in a voice channel.")
        return

    if bot_voice_channel is None:
        await ctx.send("Bot is not connected to a voice channel.")
        print(f"Bot is not connected to a voice channel.")
        return

    if user_voice_channel != bot_voice_channel:
        await ctx.send("You must be in the same voice channel as the bot to perform this action.")
        print(
            f"User {ctx.author.id} is not in the same voice channel as the bot.")
        return

    # Remove the song at the specified position (convert 1-based to 0-based index)
    try:
        removed_song = queues[ctx.guild.id].pop(position - 1)
        await ctx.send(f"Removed {removed_song[1]} from the queue.")
        print(f"Removed {removed_song[1]} from the queue.")
    except Exception as e:
        # Send an error message if something goes wrong.
        await ctx.send(f"Error: {e}")
        print(f"Error: {e}")
