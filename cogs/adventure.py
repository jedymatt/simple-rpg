import random
from datetime import datetime
from random import randint

import discord
from discord import Colour
from discord import Embed
from discord.ext import commands, menus
from sqlalchemy.orm import make_transient
from sqlalchemy.sql import func

from cogs.utils.character import add_player_item, BattleSimulator
from cogs.utils.character import create_hostile_enemy
from cogs.utils.paginator import ListPage, character_hunt_record, EmbedPages
from db.connector import session as db_session
from models import Hostile
from models import Location
from models import Modifier
from models import Player
from models import PlayerItem
from models import User
from models import util
from models.util import random_boolean


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

        random_hostile: Hostile = random.choice(hostiles)

        if player.level >= player.location.level_requirement:
            # generate level in random +2 above level of player
            random_enemy_level = random.randint(player.level, player.level + 2)
        else:
            # generate level in random -2 below level of level requirement
            random_enemy_level = random.randint(player.location.level_requirement - 2,
                                                player.location.level_requirement)

        # 40% chance of hostile with modifier appearing
        random_modifier = None
        if util.random_boolean(0.40):
            modifiers = db_session.query(Modifier).all()
            random_modifier = random.choice(modifiers)

        # disconnect from session
        make_transient(random_hostile)
        db_session.enable_relationship_loading(random_hostile)
        make_transient(random_hostile.attribute)
        make_transient(random_hostile.loot)
        db_session.enable_relationship_loading(random_hostile.loot)

        enemy = random_hostile
        create_hostile_enemy(random_enemy_level, enemy, random_modifier)
        # Battle simulation
        # first attacker is Player
        battle = BattleSimulator(player, enemy)
        winner = battle.start()
        # end simulation

        player_record = battle.character_record
        enemy_record = battle.opponent_record

        str_msg = None
        result_embed = Embed(
            title='Hunt Result:',
            colour=discord.Colour.gold()
        )

        if winner is player:
            str_msg = 'You defeated the enemy!'
            result_embed.add_field(
                name='Rewards',
                value="Money: +{}\nExp: +{}".format(
                    enemy.loot.money, enemy.loot.exp
                ),
                inline=False
            )

            # reward exp and gold
            player.exp += enemy.loot.exp
            player.money += enemy.loot.money

            has_received_item_reward = False
            # randomly generate a chance to receive drop item
            for item_loot in enemy.loot.item_loots:
                if random_boolean(item_loot.drop_chance):
                    add_player_item(player, item_loot.item, 1)
                    has_received_item_reward = True

            if has_received_item_reward:
                result_embed.add_field(
                    name='Items',
                    value="\n".join(f"{item_loot.item.name} +{1}" for item_loot in enemy.loot.item_loots)
                )

        elif winner is enemy:
            str_msg = 'You fainted!'
        else:
            if battle.character_record.has_escaped:
                str_msg = 'You escaped!'
            elif battle.opponent_record.has_escaped:
                str_msg = 'Enemy escaped!'

        result_embed.title += f"\n{str_msg}"

        entries = [
            result_embed,
            character_hunt_record('Battle Info', ctx.author.display_name, player, player_record),
            character_hunt_record('Battle Info', enemy.name, enemy, enemy_record)
        ]

        # pages = menus.MenuPages(source=ListPage(entries),
        #                         clear_reactions_after=True)
        #
        # await ctx.send(content=str_msg)
        # await pages.start(ctx)
        # await ctx.send(content=str_msg, embed=entries[1])
        pages = EmbedPages(
            msg=str_msg,
            embeds=entries
        )

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

    @commands.command()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def gather(self, ctx):
        """Gather raw materials, sometimes failed, sometimes encounter mobs"""
        author_id = ctx.author.id
        player: Player = db_session.query(Player).filter(User.discord_id == author_id).one()

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
    bot.add_cog(Adventure(bot))
