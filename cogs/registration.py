import json

from discord.ext import commands

from cogs.utils import rng
from db import session
from models import Attribute
from models import Player
from models import User

with open('data/player.json') as _json_file:
    _data = json.load(_json_file)
    _player = _data['player']
    _player_attribute = _data['attribute']


# TODO: (least priority) add task to commit every 5 minutes or so, check 'confirm' method

class Register(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.players = {}

    @commands.command()
    async def welcome(self, ctx: commands.Context):
        """Shows welcoming message to new players"""
        # sends welcoming message and intro to the game, and give instruction to roll the die
        await ctx.send("welcoming message and intro to the game, and give instruction to roll the die")

    @commands.command()
    async def roll(self, ctx: commands.Context):

        result = rng.random_dice()

        if ctx.author.id not in self.users:  # if user is not in dictionary, then create User object
            user = User(discord_id=ctx.author.id, dice_roll=result)
            self.users[ctx.author.id] = user
            session.add(user)
        else:  # else modify the init_roll
            user = self.users[ctx.author.id]
            user.dice_roll = result

        await ctx.send(str(user))

    @commands.command()
    async def confirm(self, ctx: commands.Context):
        user = self.users[ctx.author.id]
        player = Player(
            **_player
        )
        player.attribute = Attribute(
            **_player_attribute
        )
        user.player = player
        self.players[ctx.author.id] = player
        await ctx.send(str(player))

    @commands.command()
    async def commit(self, ctx):
        session.add(self.players[ctx.author.id])
        session.commit()


def setup(bot):
    bot.add_cog(Register(bot))
