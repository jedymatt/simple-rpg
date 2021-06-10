from discord.ext import commands

from db.connector import session
from models import Attribute
from models import Location
from models import Player
from models import User
from cogs.utils.character import PLAYER_DATA


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
            level=PLAYER_DATA['level'],
            exp=PLAYER_DATA['exp'],
            money=PLAYER_DATA['money'],
            attribute=Attribute(
                **PLAYER_DATA['attribute']
            ),
            location=session.query(Location).filter(Location.name == PLAYER_DATA['location']).one()
        )

        session.add(user)
        session.commit()


def setup(bot):
    bot.add_cog(Register(bot))
