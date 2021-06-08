import json

from discord.ext import commands

from db import session
from models import Attribute
from models import Location
from models import Player
from models import User

with open('data/player.json') as _json_file:
    player_data = json.load(_json_file)


class Register(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def create(self, ctx):
        user = User(
            discord_id=ctx.author.id
        )
        Player(
            user=user,
            level=player_data['level'],
            exp=player_data['exp'],
            money=player_data['money'],
            attribute=Attribute(
                **player_data['attribute']
            ),
            location=session.query(Location).filter(Location.name == player_data['location']).one()
        )

        session.add(user)
        session.commit()


def setup(bot):
    bot.add_cog(Register(bot))
