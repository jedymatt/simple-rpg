import random
from datetime import datetime
from random import randint

from discord import Colour
from discord import Embed
from discord.ext import commands
from sqlalchemy.orm import make_transient
from sqlalchemy.sql import func

from cogs.utils.character import add_player_item, BattleSimulator
from cogs.utils.character import adjust_hostile_by_level
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
    async def hunt(self, ctx):
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
        adjust_hostile_by_level(random_enemy_level, enemy, random_modifier)
        # Battle simulation
        # first attacker is Player
        battle = BattleSimulator(player, enemy)
        winner = battle.start()
        # end simulation

        player_record = battle.character_record
        enemy_record = battle.opponent_record

        # embed
        embed = Embed(
            title='Hunt Info',
        )

        embed.add_field(
            name=f"{ctx.author.display_name} Lvl.{player.level}",
            value="HP: {} / {}\nAve. Dmg/hit: {}\nHighest Dmg: {}{}\nCrit Hit(s): {}\nEvaded Hit(s): {}\n"
                  "Lowest Damage Received: {}".format(player_record.current_hp if player_record.current_hp > 0 else 0,
                                                      player.attribute.max_hp,
                                                      round(player_record.total_damage_dealt / player_record.total_hits,
                                                            1),
                                                      'Crit ' if player_record.highest_damage_is_crit else '',
                                                      player_record.highest_damage,
                                                      player_record.crit_hits,
                                                      player_record.evaded_hits,
                                                      player_record.lowest_damage_received),
            # inline=False
        )

        embed.add_field(
            name=f"{enemy.name} Lvl.{enemy.level}",
            value="HP: {} / {}\nAve. Dmg/hit: {}\nHighest Dmg: {}{}\nCrit Hit(s): {}\nEvaded Hit(s): {}\n"
                  "Lowest Damage Received: {}".format(enemy_record.current_hp if enemy_record.current_hp > 0 else 0,
                                                      enemy.attribute.max_hp,
                                                      round(enemy_record.total_damage_dealt / enemy_record.total_hits,
                                                            1),
                                                      'Crit ' if enemy_record.highest_damage_is_crit else '',
                                                      enemy_record.highest_damage,
                                                      enemy_record.crit_hits,
                                                      enemy_record.evaded_hits,
                                                      enemy_record.lowest_damage_received),
            inline=False
        )

        if winner is player:

            # randomly generate a chance to receive drop item
            for item_loot in enemy.loot.item_loots:
                if random_boolean(item_loot.drop_chance):
                    add_player_item(player, item_loot.item, 1)

            await ctx.send('You won.', embed=embed)
        elif winner is enemy:
            await ctx.send('Defeat', embed=embed)
        else:
            if battle.character_record.has_escaped:
                await ctx.send('You escaped', embed=embed)
            elif battle.opponent_record.has_escaped:
                await ctx.send('Enemy escaped', embed=embed)

        print(random_hostile)
        print(random_hostile.attribute)
        print(random_hostile.loot)
        print('------------------------------')
        print('Session.dirty =', db_session.dirty)
        print('Session.new =', db_session.new)

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
