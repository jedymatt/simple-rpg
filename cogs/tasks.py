import asyncio

from discord.ext import tasks, commands

from db import session
from models import Player, User


class BackgroundTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.commit.start()

    @tasks.loop(minutes=10)
    async def commit(self):
        print('Committing...')
        print('Session.new:', session.new)
        print('Session.dirty:', session.dirty)
        session.commit()
        print('Committed')

    @commit.before_loop
    async def before_commit(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(600)

    def cog_unload(self):
        self.commit.cancel()

    @commands.command(name='commit')
    async def commit_(self, ctx):
        session.commit()

    @commands.command()
    async def delete(self, ctx):
        player = (
            session.query(Player).join(User, User.player_id == Player.id)
                .where(User.discord_id == ctx.author.id).one()
        )
        session.delete(player)


def setup(bot: commands.Bot):
    bot.add_cog(BackgroundTask(bot))
