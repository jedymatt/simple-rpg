import random
from random import randint

import discord
from discord import Colour
from discord import Embed
from discord.ext import commands
from discord.ext import menus
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import noload, joinedload
from sqlalchemy.sql import func

from cogs.utils import images, errors
from cogs.utils import player as pl
from cogs.utils.character import BattleSimulator, NameAmount
from cogs.utils.character import adjust_hostile_enemy
from cogs.utils.character import level_up
from cogs.utils.character import next_exp
from cogs.utils.character import player_changed_attribute
from cogs.utils.character import random_boolean
from cogs.utils.paginator import EmbedListPage, LocationListPage
from cogs.utils.paginator import record_embed
from cogs.utils.query import get_player, get_hostile, get_modifier
from db import session
from models import Hostile, Loot, LocationLoot, ItemLoot
from models import Location
from models import Modifier
from models import Player
from models import PlayerItem
from models import User


class Adventure(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['go', 'travel', 'travelto', 'venture', 'ventureto'])
    async def goto(self, ctx, *, location: str):
        """Travel to a specific location"""
        author_id = ctx.author.id

        try:
            location = session.query(Location).filter(
                func.lower(Location.name) == location.lower()
            ).one()
        except NoResultFound:
            raise commands.UserInputError(f"\"{location}\" not found, try again.")

        if location is None:
            raise commands.UserInputError('Location not found. Try again.')

        player: Player = session.query(Player).options(
            noload(Player.attribute),
            noload(Player.items)
        ).join(User).filter(
            User.discord_id == author_id
        ).one()

        if player.level >= location.level_requirement:
            player.location = location
        else:
            raise errors.LevelNotReached(f"Can't to venture to \"{location.name}\"")

        await ctx.send('success')

    @goto.error
    async def goto_error(self, ctx, error):
        if isinstance(error, errors.LevelNotReached):
            embed = Embed(
                colour=discord.Colour.red(),
                title=error.args[0]
            )
            embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.avatar_url
            )

            embed.description = "Your level is too low, and you might get hurt the during your travel. " \
                                "Don't worry! You can try again when you're strong enough."
            await ctx.send(embed=embed)
        elif isinstance(error, commands.UserInputError):
            await ctx.send(error.args[0])

        else:
            raise error

    @commands.command()
    async def hunt(self, ctx: commands.Context):
        """Explore the surrounding"""
        player = get_player(session, ctx.author.id)
        # find IDs of Hostile(s) in the current location of the Player,
        # then generate & select random hostile
        hostile_ids = session.query(Hostile.id).join(Location).filter(
            Location.id == player.location.id
        ).all()
        random_hostile_id = random.choice(hostile_ids).id
        enemy = get_hostile(session, random_hostile_id, make_transient_=True)

        if player.level >= player.location.level_requirement:
            # generate level in random +2 above level of player
            new_level = random.randint(player.level, player.level + 2)
        else:
            # generate level in random -2 below level of level requirement
            new_level = random.randint(player.location.level_requirement - 2,
                                       player.location.level_requirement)

        # 40% chance of hostile with modifier appearing
        modifier = None
        if random_boolean(0.40):
            modifier_ids = session.query(Modifier.id).all()
            modifier_id = random.choice(modifier_ids).id
            modifier = get_modifier(session, modifier_id)

        # adjust attribute of enemy according to its level
        adjust_hostile_enemy(new_level, enemy, modifier)

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
                value="Exp +{}\nMoney +{}".format(
                    enemy.loot.exp, enemy.loot.money
                ),
                inline=False
            )

            # reward exp and gold
            player.money += enemy.loot.money
            player.exp += enemy.loot.exp

            rewards = []
            # randomly generate a chance to receive drop item
            for item_loot in enemy.loot.item_loots:
                if random_boolean(item_loot.drop_chance):
                    random_amount = randint(item_loot.min, item_loot.max)
                    pl.add_item(player.items, item_loot.item, random_amount)

                    rewards.append(
                        NameAmount(
                            name=item_loot.item.name,
                            amount=random_amount
                        )
                    )

            if len(rewards) != 0:
                result_embed.add_field(
                    name='Items',
                    value="\n".join(f"{reward.name} +{reward.amount}" for reward in rewards),
                    inline=False
                )

            if player.exp >= next_exp(player.level):
                old_level = player.level
                raised_level = level_up(player)
                raised_attribute = player_changed_attribute(old_level, player.level)
                pl.player_scale_attribute(player.level, player.attribute)

                raised_values = [
                    ('New Level: {}', [player.level]),
                    ('Max HP +{}', [raised_attribute.max_hp]),
                    ('Strength +{}', [raised_attribute.strength]),
                    ('Defense +{}', [raised_attribute.defense])
                ]

                result_embed.add_field(
                    name=f"You leveled up by {raised_level}",
                    value="\n".join(value[0].format(*value[1]) for value in raised_values)
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
        entries = [
            result_embed,
            record_embed('Performance', ctx.author.display_name, player, player_record,
                         thumbnail_url=ctx.author.avatar_url),
            record_embed('Performance', enemy.name, enemy, enemy_record)
        ]

        for entry in entries:
            entry.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        pages = menus.MenuPages(
            source=EmbedListPage(global_message=str_message, embeds=entries),
            clear_reactions_after=True,
        )

        # db_session.commit()
        await pages.start(ctx)

    @commands.command(aliases=['places', 'areas'])
    async def locations(self, ctx):
        locations = session.query(Location).all()

        pages = menus.MenuPages(source=LocationListPage(entries=locations),
                                clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command()
    # @commands.cooldown(1, 60, commands.BucketType.user)
    async def gather(self, ctx):
        """Gather raw materials, sometimes fails, sometimes encounters mobs"""
        player, loot = session.query(Player, Loot) \
            .select_from(Player) \
            .join(Location, Location.id == Player.location_id) \
            .join(LocationLoot, Location.id == LocationLoot.location_id) \
            .join(Loot, Loot.id == LocationLoot.loot_id) \
            .join(User, User.player_id == Player.id) \
            .options(joinedload(Player.location),
                     joinedload(Player.items).subqueryload(PlayerItem.item),
                     joinedload(Loot.item_loots).subqueryload(ItemLoot.item)) \
            .filter(User.discord_id == ctx.author.id).one()

        gains = [('Money', loot.money)]
        player.money += loot.money

        for item_loot in loot.item_loots:
            success = random_boolean(item_loot.drop_chance)

            if success:
                item = item_loot.item
                amount = randint(item_loot.min, item_loot.max)
                gains.append((item.name, amount))
                # add the item and amount to player.items
                pl.add_item(player_items=player.items, item=item, amount=amount)

        # declare embed
        embed = Embed(
            title='Obtained',
            colour=Colour.green()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.description = "\n".join(f"{gain[0]} +{gain[1]}" for gain in gains)

        # send output
        await ctx.send(embed=embed)

    @gather.error
    async def gather_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error.args)
        else:
            raise error


def setup(bot: commands.Bot):
    bot.add_cog(Adventure(bot))
