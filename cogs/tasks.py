import asyncio

from discord.ext import tasks, commands

from db.connector import session


class BackgroundTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        await asyncio.sleep(600)
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

    def cog_unload(self):
        self.commit.cancel()

    @commands.command(name='commit')
    async def commit_(self, ctx):
        session.commit()


def setup(bot: commands.Bot):
    bot.add_cog(BackgroundTask(bot))
