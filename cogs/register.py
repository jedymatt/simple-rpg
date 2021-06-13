from discord.ext import commands

from db.connector import session
from models import Attribute, User, Location, Player
from cogs.utils.character import PLAYER_INITIAL_DATA


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
            level=PLAYER_INITIAL_DATA['level'],
            exp=PLAYER_INITIAL_DATA['exp'],
            money=PLAYER_INITIAL_DATA['money'],
            attribute=Attribute(
                **PLAYER_INITIAL_DATA['attribute']
            ),
            location=session.query(Location).filter(Location.name == PLAYER_INITIAL_DATA['location']).one()
        )

        session.add(user)
        session.commit()


def setup(bot):
    bot.add_cog(Register(bot))
