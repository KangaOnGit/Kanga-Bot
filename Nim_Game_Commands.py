import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import os
from Settings import bot
# Store lobbies
lobbies = {}
class NimGame:
    def __init__(self, player1, player2, max_sticks=15, max_take=3):
        self.total_sticks = max_sticks
        self.max_take = max_take
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1

    def remove_sticks(self, count):
        self.total_sticks -= count

    def switch_player(self):
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1

    def is_game_over(self):
        return self.total_sticks <= 0


class NimView(View):
    def __init__(self, game, ctx):
        super().__init__()
        self.game = game
        self.ctx = ctx

    async def interaction_check(self, interaction):
        return interaction.user == self.game.current_player

    @discord.ui.button(label="Take 1", style=discord.ButtonStyle.primary)
    async def take_one(self, interaction: discord.Interaction, button: Button):
        await self.take_sticks(interaction, 1)

    @discord.ui.button(label="Take 2", style=discord.ButtonStyle.primary)
    async def take_two(self, interaction: discord.Interaction, button: Button):
        await self.take_sticks(interaction, 2)

    @discord.ui.button(label="Take 3", style=discord.ButtonStyle.primary)
    async def take_three(self, interaction: discord.Interaction, button: Button):
        await self.take_sticks(interaction, 3)

    async def take_sticks(self, interaction, count):
        self.game.remove_sticks(count)
        if self.game.is_game_over():
            await self.ctx.send(f"{interaction.user.mention} took the last stick! {interaction.user.mention} wins!")
            await self.ctx.send("Do you want to replay?", view=ReplayView(self.ctx, self.game))
            self.stop()
        else:
            self.game.switch_player()
            await interaction.response.edit_message(content=f"{self.game.current_player.mention}'s turn. Sticks remaining: {self.game.total_sticks}")


class ReplayView(View):
    def __init__(self, ctx, game):
        super().__init__()
        self.ctx = ctx
        self.game = game
        self.replay_votes = {game.player1.id: False, game.player2.id: False}

    async def check_replay_votes(self):
        if all(self.replay_votes.values()):
            await self.ctx.send("Both players agreed! Starting a new game...")
            await start_nim_game(self.ctx, self.game.player1, self.game.player2)

    @discord.ui.button(label="Replay", style=discord.ButtonStyle.success)
    async def replay(self, interaction: discord.Interaction, button: Button):
        self.replay_votes[interaction.user.id] = True
        await interaction.response.send_message(f"{interaction.user.mention} voted to replay.", ephemeral=True)
        await self.check_replay_votes()

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.danger)
    async def exit(self, interaction: discord.Interaction, button: Button):
        del lobbies[self.game.player1.id]
        await interaction.response.edit_message(content="Game ended. Lobby closed.", view=None)


@bot.command(name='nim')
async def nim_lobby(ctx, opponent: discord.Member = None):
    if opponent:
        if opponent.id in lobbies and lobbies[opponent.id]['status'] == 'waiting':
            lobbies[opponent.id]['opponent'] = ctx.author
            lobbies[opponent.id]['status'] = 'in_progress'
            await ctx.send(f"{ctx.author.mention} joined {opponent.mention}'s lobby. The game is starting!")
            await start_nim_game(ctx, lobbies[opponent.id]['host'], ctx.author)
        else:
            await ctx.send(f"{opponent.mention} doesn't have an open lobby or is already in a game.")
    else:
        if ctx.author.id not in lobbies:
            lobbies[ctx.author.id] = {
                'host': ctx.author.id, 'opponent': None, 'status': 'waiting'}
            await ctx.send(f"{ctx.author.mention} created a Nim game lobby. Waiting for an opponent...")
        else:
            await ctx.send(f"{ctx.author.mention}, you already have a lobby open.")


@bot.command(name='nim_cancel')
async def nim_cancel(ctx):
    if ctx.author.id in lobbies and lobbies[ctx.author.id]['host'] == ctx.author:
        del lobbies[ctx.author.id]
        await ctx.send(f"{ctx.author.mention}, your lobby has been canceled.")
    else:
        await ctx.send(f"{ctx.author.mention}, you don't have a lobby to cancel, or you are not the host.")


@bot.command(name='nim_leave')
async def nim_leave(ctx):
    for lobby_id, lobby in lobbies.items():
        if lobby['opponent'] == ctx.author:
            lobbies[lobby_id]['opponent'] = None
            lobbies[lobby_id]['status'] = 'waiting'
            await ctx.send(f"{ctx.author.mention}, you have left the game. The lobby is now waiting for a new opponent.")
            return
    await ctx.send(f"{ctx.author.mention}, you are not in any active game.")


async def start_nim_game(ctx, player1, player2):
    game = NimGame(player1, player2)
    await ctx.send(f"Nim game starting between {player1.mention} and {player2.mention}!")
    await ctx.send(f"{game.current_player.mention}'s turn. Sticks remaining: {game.total_sticks}", view=NimView(game, ctx))


@bot.command(name='nim_lobbies')
async def view_lobbies(ctx):
    if lobbies:
        embed = discord.Embed(title="Active Nim Lobbies", colour=0x5865F2)
        for lobby_id, lobby in lobbies.items():
            host = await bot.fetch_user(lobby["host"])
            opponent = lobby['opponent'].mention if lobby['opponent'] else "Waiting for opponent..."
            status = lobby['status'].capitalize()
            embed.add_field(name=f"Lobby by {host}", value=f"Opponent: {
                            opponent}\nStatus: {status}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("There are no active lobbies at the moment.")
