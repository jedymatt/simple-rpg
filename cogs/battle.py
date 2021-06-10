import discord
from discord.ext import commands

from db.connector import session
from models import Player
from models import User


class Battle(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def spar(self, ctx: commands.Context, challenged: discord.Member):
        """

        Start a practice match with a player, no exp can be earned on both sides

        """

        player: Player = session.query(Player).join(User).filter(User.discord_id == ctx.author.id).one()
        opponent: Player = session.query(Player).join(User).filter(User.discord_id == challenged.id).one()

        player_dmg = opponent.take_damage(player.strength)
        opponent_dmg = player.take_damage(opponent.strength)

        # restore hp
        player.current_hp += player_dmg
        opponent.current_hp += player_dmg

        if player_dmg == opponent_dmg:
            await ctx.send('It is a draw!')
        else:
            await ctx.send(
                f'{ctx.author}: {player_dmg} pts\n'
                f'{challenged}: {opponent_dmg} pts\n'
                f'The winner is {ctx.author if player_dmg > opponent_dmg else challenged}'
            )


def setup(bot):
    bot.add_cog(Battle(bot))
