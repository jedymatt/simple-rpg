import discord
from discord.ext import commands

from cogs.utils.character import next_exp
from cogs.utils.query import get_player
from db.connector import session


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def profile(self, ctx: commands.Context):
        """Show profile"""

        player = get_player(session, discord_id=ctx.author.id)

        # Embedded format
        embed = discord.Embed(
            title="PROFILE",
            colour=discord.Colour.orange(),
        )

        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.author.avatar_url)

        embed.add_field(
            name='Details',
            value="Level: {}\nExp: {} / {}\nMoney: {}\nLocation: *{}*".format(
                player.level,
                player.exp,
                next_exp(player.level),
                player.money,
                player.location.name
            ),
            inline=False
        )

        stats = player.attribute

        embed.add_field(
            name='Stats',
            value="Max HP: {}\nStrength: {}\nDefense: {}\nCrit Chance: {}%\n"
                  "Crit Dmg: {}%\nEvade: {}%\nEscape: {}%".format(stats.max_hp,
                                                                  stats.strength,
                                                                  stats.defense,
                                                                  stats.critical_chance * 100,
                                                                  stats.critical_damage * 100,
                                                                  stats.evade_chance * 100,
                                                                  stats.escape_chance * 100),
            inline=False
        )

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Information(bot))
