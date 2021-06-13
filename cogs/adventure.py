import random
from datetime import datetime
from random import randint

import discord
from discord import Colour
from discord import Embed
from discord.ext import commands
from discord.ext import menus
from sqlalchemy.orm import make_transient
from sqlalchemy.sql import func

import cogs.utils.character
from cogs.utils import images
from cogs.utils.character import BattleSimulator
from cogs.utils.character import add_player_item
from cogs.utils.character import adjust_hostile_enemy
from cogs.utils.character import next_exp
from cogs.utils.character import random_boolean
from cogs.utils.errors import MaximumExpError
from cogs.utils.paginator import EmbedListPage
from cogs.utils.paginator import record_embed
from db.connector import session as db_session
from models import Hostile
from models import Location
from models import Modifier
from models import Player
from models import PlayerItem
from models import User


class Adventure(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def travel(self, ctx, location: str):
        """Travel to a specific location"""
        author_id = ctx.author.id

        location: Location = db_session.query(Location).filter(
            func.lower(Location.name) == location.lower()
        ).one()

        player: Player = db_session.query(Player).join(User).filter(User.discord_id == author_id).one()

        if player.level >= location.level_requirement:
            player.location = location
        else:
            raise ValueError('Your level is low.')

        await ctx.send('success')

    @commands.command()
    async def hunt(self, ctx: commands.Context):
        """Explore the surrounding"""
        player = db_session.query(Player).join(User).filter(
            User.discord_id == ctx.author.id
        ).one()

        # find Hostile(s) in the current location of the Player
        hostiles = db_session.query(Hostile).join(Location).filter(
            Location.id == player.location.id
        ).all()

        enemy: Hostile = random.choice(hostiles)

        if player.level >= player.location.level_requirement:
            # generate level in random +2 above level of player
            new_level = random.randint(player.level, player.level + 2)
        else:
            # generate level in random -2 below level of level requirement
            new_level = random.randint(player.location.level_requirement - 2,
                                       player.location.level_requirement)

        # 40% chance of hostile with modifier appearing
        enemy_modifier = None
        if cogs.utils.character.random_boolean(0.40):
            modifiers = db_session.query(Modifier).all()
            enemy_modifier = random.choice(modifiers)

        # disconnect obj from session to avoid saving the data to the database
        # assigning temporary variables to avoid becoming None when executing make_transient()
        _ = enemy
        _ = enemy.attribute
        _ = enemy.loot
        _ = enemy.loot.item_loots
        make_transient(enemy)
        make_transient(enemy.attribute)
        make_transient(enemy.loot)

        # adjust attribute of enemy according to its level
        adjust_hostile_enemy(new_level, enemy, enemy_modifier)

        # Battle simulation
        # first attacker is Player
        battle = BattleSimulator(player, enemy)
        winner = battle.start()
        # end simulation
        # records of the battle
        player_record = battle.character_record
        enemy_record = battle.opponent_record

        str_message = ''
        result_embed = Embed(
            title='Hunt Result:',
            colour=discord.Colour.gold()
        )

        if winner is player:
            str_message = 'You defeated the enemy!'
            result_embed.add_field(
                name='Rewards',
                value="Exp: +{}\nMoney: +{}".format(
                    enemy.loot.exp, enemy.loot.money
                ),
                inline=False
            )

            # reward exp and gold
            player.money += enemy.loot.money
            player.exp += enemy.loot.exp
            if player.exp >= next_exp(player.level):
                raise MaximumExpError('Exp cap reached')

            has_received_item_reward = False
            # randomly generate a chance to receive drop item
            for item_loot in enemy.loot.item_loots:
                if random_boolean(item_loot.drop_chance):
                    add_player_item(player.items, item_loot.item, 1)
                    has_received_item_reward = True

            if has_received_item_reward:
                result_embed.add_field(
                    name='Items',
                    value="\n".join(f"{item_loot.item.name} +{1}" for item_loot in enemy.loot.item_loots)
                )

        elif winner is enemy:
            str_message = 'You fainted!'
        else:
            if battle.character_record.has_escaped:
                str_message = 'You escaped!'
            elif battle.opponent_record.has_escaped:
                str_message = 'Enemy escaped!'

        result_embed.description = str_message
        result_embed.set_thumbnail(url=images.DEFAULT)
        result_embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        entries = [
            result_embed,
            record_embed('Performance', ctx.author.display_name, player, player_record,
                         thumbnail_url=ctx.author.avatar_url),
            record_embed('Battle Info', enemy.name, enemy, enemy_record)
        ]

        pages = menus.MenuPages(
            source=EmbedListPage(global_message=str_message, embeds=entries),
            clear_reactions_after=True)

        await pages.start(ctx)

    @commands.command(aliases=['places', 'areas'])
    async def locations(self, ctx):
        locations = db_session.query(Location).all()
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

    # TODO: Fix gather command
    @commands.command()
    # @commands.cooldown(1, 60, commands.BucketType.user)
    async def gather(self, ctx):
        """Gather raw materials, sometimes failed, sometimes encounter mobs"""
        author_id = ctx.author.id
        player: Player = db_session.query(Player).filter(User.discord_id == author_id).one()

        gathered = []
        location: Location = player.location
        for raw_material in location.raw_materials:

            success = cogs.utils.character.random_boolean(raw_material.drop_chance)

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
    bot.add_cog(Adventure(bot))
