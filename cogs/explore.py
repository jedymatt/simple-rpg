import copy
import random
from datetime import datetime
from math import ceil
from random import randint

from discord import Colour
from discord import Embed
from discord.ext import commands
from sqlalchemy.sql import func

from cogs.utils.character import combine_attributes, scale_loot, gain_exp
from db.connector import session
from models import Hostile, Loot
from models import Location
from models import Modifier
from models import Player
from models import PlayerItem
from models import User
from models import util
from models.util import character_scale_attribute


class Explore(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def travel(self, ctx, location: str):
        """Travel to a specific location"""
        author_id = ctx.author.id

        location: Location = session.query(Location).filter(
            func.lower(Location.name) == location.lower()
        ).one()

        player: Player = session.query(Player).join(User).filter(User.discord_id == author_id).one()

        if player.level >= location.level_requirement:
            player.location = location
        else:
            raise ValueError('Your level is low.')

        await ctx.send('success')

    @commands.command()
    async def hunt(self, ctx):
        """Explore the surrounding"""
        player = session.query(Player).join(User).filter(
            User.discord_id == ctx.author.id
        ).one()

        # find Hostile(s) in the current location of the Player
        hostiles = session.query(Hostile).join(Location).filter(
            Location.id == player.location.id
        ).all()

        chosen_hostile: Hostile = random.choice(hostiles)

        if player.level >= player.location.level_requirement:
            # generate level in random +2 above level of player
            enemy_level = random.randint(player.level, player.level + 2)
        else:
            # generate level in random -2 below level of level requirement
            enemy_level = random.randint(player.location.level_requirement - 2, player.location.level_requirement)

        enemy = Hostile(level=enemy_level, exp=0)

        enemy.loot = Loot(
            exp=chosen_hostile.loot.exp,
            money=chosen_hostile.loot.money
        )

        # 45% chance of hostile with modifier appearing
        if util.random_boolean(.45):
            modifiers = session.query(Modifier).all()
            chosen_modifier: Modifier = random.choice(modifiers)
            enemy.name = "{} {}".format(chosen_modifier.prefix, chosen_hostile.name)
            enemy.attribute = combine_attributes(chosen_hostile.attribute, chosen_modifier.attribute)
            enemy.loot.exp = ceil(enemy.loot.exp * (1 + chosen_modifier.bonus_exp))
            enemy.loot.money = ceil(enemy.loot.money * (1 + chosen_modifier.bonus_money))
        else:
            enemy.name = chosen_hostile.name
            enemy.attribute = copy.copy(chosen_hostile.attribute)

        # scale attribute to match the level
        character_scale_attribute(enemy.level, enemy.attribute)
        # scale loot
        scale_loot(enemy.level, enemy.loot)

        print(player, end=f"\n{player.attribute}")
        print('vs.')
        print(enemy, end=f"\n{enemy.attribute}")

        # Battle simulation
        # first attacker is Player
        player_turn = True
        player_hp = player.attribute.max_hp
        enemy_hp = enemy.attribute.max_hp

        while player_hp > 0 and enemy_hp > 0:

            if player_turn:
                damage_dealt = util.calculate_damage(player.attribute, enemy.attribute)
                enemy_hp -= damage_dealt[0]
                player_turn = False
            else:
                damage_dealt = util.calculate_damage(enemy.attribute, player.attribute)
                player_hp -= damage_dealt[0]
                player_turn = True

            # print('{}: {}{}'.format(ctx.author.name if not player_turn else enemy.name,
            #                         "Crit " if damage_dealt[1] else "",
            #                         damage_dealt[0]))
        # end simulation

        print("Player HP: {}, Enemy HP: {}".format(player_hp, enemy_hp))
        print('{} won.'.format(ctx.author.name if player_hp > 0 else enemy.name))
        # if player won
        if player_hp > 0:
            print('rewards')
            print('exp:', enemy.loot.exp)
            print('money:', enemy.loot.money)
            player.money += enemy.loot.money
            player.exp += enemy.loot.exp
            # todo: add code here to check if the player exp reached the amount of exp required
            #  to level up

            # randomly generate a chance to receive drop item
            for item_loot in chosen_hostile.loot.item_loots:
                # todo: add code or create and call the function here to add player item
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
                value=location.description if location.description else '*No description yet*',
                inline=False
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
            await self.hunt(ctx)

        # send output
        await ctx.send(str(gathered))

    @gather.error
    async def gather_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error.args)
        else:
            raise error


def setup(bot: commands.Bot):
    bot.add_cog(Explore(bot))
