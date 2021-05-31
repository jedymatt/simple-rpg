from datetime import datetime
from random import randint

from discord import Colour
from discord import Embed
from discord.ext import commands
from sqlalchemy.sql import func

from db import session
from models import Hostile
from models import Location
from models import Player
from models import PlayerItem
from models import User
from models import util


class Exploration(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def goto(self, ctx, location: str):
        """Go to the specific location"""
        author_id = ctx.author.id

        location: Location = session.query(Location).filter(
            func.lower(Location.name) == location.lower()).one()

        player: Player = session.query(Player).join(User).filter(User.discord_id == author_id).one()

        if player.level >= location.unlock_level:
            player.location = location
        else:
            raise ValueError('Location is not yet unlocked.')

        await ctx.send('success')

    @commands.command()
    async def explore(self, ctx):
        """Explore the location"""
        pass

    @commands.command(aliases=['places', 'areas'])
    async def locations(self, ctx):
        locations = session.query(Location).all()
        embed = Embed(
            title='Locations',
            colour=Colour.dark_green(),
            timestamp=datetime.now()
        )

        for location in locations:
            embed.add_field(
                name=location.name,
                value=location.description if location.description else '*No description yet*'
            )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def gather(self, ctx):
        """Gather raw materials, sometimes failed, sometimes encounter mobs"""
        author_id = ctx.author.id
        player: Player = session.query(Player).filter(User.discord_id == author_id).one()

        gathered = []
        location: Location = player.location
        for raw_material in location.raw_materials:

            success = util.random_boolean(raw_material.drop_chance)

            if success:
                drop_min = raw_material.drop_amount_min
                drop_max = raw_material.drop_amount_max
                gathered.append((raw_material.raw_material, randint(drop_min, drop_max)))

        # declare embed
        embed = Embed(
            title='Gathered',
            colour=Colour.green()
        )

        for gather in gathered:
            # get player_item if none found then value is None
            player_item = next(
                (player_item for player_item in player.items if player_item.item == gather[0]),
                None
            )

            # add item to Player.items
            if player_item:
                player_item.amount += gather[1]
            else:
                # if none, create obj and append it to the Player.items
                player.items.append(
                    PlayerItem(
                        item=gather[0],
                        amount=gather[1]
                    )
                )

            # add embed field
            embed.add_field(
                name=gather[0].name,
                value="+%s" % gather[1]
            )

        # if player has not gained anything, a monster appears
        if gathered is None:
            await ctx.send("A monster appeared! You are forced to fight.")
            # generate monster depending on the place
            monster = session.query(Hostile).filter(Hostile.location.name == player.location).one()

            player_dmg = monster.take_damage(player.strength)
            monster_dmg = player.take_damage(monster.strength)

            if player_dmg > monster_dmg:
                exp_gained = 25  # this value is not final
                await ctx.send(f'You defeated the monster. You gained {exp_gained}xp')
                player.add_exp(exp_gained)
            elif player_dmg > monster_dmg:
                exp_lost = 5  # # this value is not final
                await ctx.send(f'You are defeated. You lost {exp_lost}exp')
                player.reduce_exp(exp_lost)
            else:
                await ctx.send('The monster ran away.')

        # send output
        await ctx.send(str(gathered))

    @gather.error
    async def gather_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error.args)
        else:
            raise error

    @commands.command()
    async def hunt(self, ctx):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(Exploration(bot))
