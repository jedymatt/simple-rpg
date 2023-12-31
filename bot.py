from discord.ext import commands

from config import BOT_TOKEN
from db import engine

cogs = [
    'register',
    'adventure',
    'information',
    'inventory',
    'tasks'
]


class SimpleRPG(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix='.',
            case_insensitive=True
        )

        for cog in cogs:
            self.load_extension(f'cogs.{cog}')


def main():
    bot = SimpleRPG()

    @bot.event
    async def on_ready():
        print(f'Logged in as {bot.user}')

    @bot.command()
    async def ping(ctx: commands.Context):
        await ctx.send(f'Ping: `{round(bot.latency, 2)}ms`')

    # connect to database
    engine.connect()

    # run bot
    bot.run(BOT_TOKEN)


if __name__ == '__main__':
    # print(os.getcwd())
    main()
