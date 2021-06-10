import random

import discord
from discord.ext import commands

from cogs.utils.errors import ItemNotFound
from cogs.utils.stripper import strip_name_amount
from db.connector import session
from models import Attribute
from models import ItemPlan, Equipment, ShopItem, PlayerItem, Player, User, Consumable, Weapon, Shield, EquipmentSet


class ItemCommand(commands.Cog, name='Manage Items'):

    def __init__(self, bot):
        self.bot = bot
        self.item_plans = session.query(ItemPlan).all()
        self.shop_items = session.query(ShopItem).all()

    @commands.command()
    async def items(self, ctx):
        """Show list of items"""
        author_id = ctx.author.id

        player = session.query(Player).filter(User.discord_id == author_id).one()

        embed = discord.Embed(
            title='Owned Items',
            colour=discord.Colour.random()
        )

        for player_item in player.items:
            if not isinstance(player_item.item, Equipment):
                embed.add_field(
                    name=player_item.item.name,
                    value="+%s" % player_item.amount
                )

        await ctx.send(embed=embed)

    @commands.command(aliases=['craftables', 'plans', 'plan'])
    async def craftable(self, ctx: commands.Context):
        """Show list of craftable items"""

        embed = discord.Embed(
            title='Craftable Items with Materials',
            colour=discord.Colour.purple()
        )

        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

        for item_plan in self.item_plans:
            msg = '\n'.join([f"{mat.amount} {mat.item.name}" for mat in item_plan.materials])

            embed.add_field(
                name=item_plan.item.name,
                value=msg
            )

        await ctx.send(content=f'**{ctx.author.name}**', embed=embed)

    @commands.command()
    async def craft(self, ctx: commands.Context, *, arg: str):
        name, amount = strip_name_amount(arg)
        author_id = ctx.author.id

        # search for matched plan in plans
        # item_plan = next((item_plan for item_plan in self.item_plans if name.lower() == item_plan.name.lower()), None)

        try:
            # search for matched plan in plans
            item_plan = next(item_plan for item_plan in self.item_plans if name.lower() == item_plan.name.lower())
        except StopIteration:
            raise ItemNotFound('Item not found')

        player = session.query(Player).filter(User.discord_id == author_id).one()

        new_amounts = {}
        success = True
        lack_materials = []
        for material in item_plan.materials:
            # total amount of material
            material_amount = material.amount * amount
            # get player_item that matches material
            player_item: PlayerItem = next(
                (player_item for player_item in player.items if material.item == player_item.item), None)

            if player_item:
                if player_item.amount < material_amount:
                    success = False  # raise an error or count how much is lacking
                    lack_materials.append({'item': player_item.name,
                                           'lack': player_item.amount - material_amount
                                           })
                else:
                    new_amounts[material.item.name] = player_item.amount - material_amount

            else:
                success = False  # no matched player_item in the plan_materials
                lack_materials.append({'item': material.item.name,
                                       'lack': - material_amount
                                       })

        if success:  # if success, overwrite amounts

            for player_item in player.items:
                if player_item.item.name in new_amounts:
                    player_item.amount = new_amounts[player_item.item.name]

            if item_plan.item not in player.items:
                new_player_item = PlayerItem(item=item_plan.item, amount=amount)
                player.items.append(new_player_item)
            else:
                item = next(item for item in player.items if item == item_plan.item)
                item.amount += amount

            await ctx.send('success')

        else:
            embed = discord.Embed(
                title='Craft failed',
                colour=discord.Colour.dark_red()
            )

            msg = '\n'.join(f"{lack['lack']} {lack['item']}" for lack in lack_materials)

            embed.add_field(
                name='Missing materials',
                value=msg
            )

            await ctx.send(embed=embed)

    @craft.error
    async def craft_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please specify the item:')
            await self.craftable(ctx)
        if isinstance(error, ItemNotFound):
            await ctx.send('Invalid item')

        raise error

    @commands.command()
    async def equip(self, ctx, *, arg: str):
        name = arg.lower()

        player = session.query(Player).filter(User.discord_id == ctx.author.id).one()

        try:
            player_item = next(
                player_item for player_item in player.items if
                str(player_item.item.name).lower() == name
            )
        except StopIteration:
            raise ValueError('No equipment found')

        if not isinstance(player_item.item, Equipment):
            raise ValueError('Item is not an equipment')

        # # if not found throws sqlalchemy.orm.exc.NoResultFound
        # equipment = session.query(Equipment).filter(PlayerItem.player_id == player.id).filter(
        #     func.lower(Equipment.name) == name.lower()
        # ).one()

        if player_item.amount == 0:
            raise ValueError('Amount not enough')

        if not player.equipment_set:
            player.equipment_set = EquipmentSet()

        if isinstance(player_item.item, Weapon):
            if player.equipment_set.weapon is not None:
                player.attribute -= player.equipment_set.weapon.attribute

            player.equipment_set.weapon = player_item.item
        elif isinstance(player_item.item, Shield):
            if player.equipment_set.shield is not None:
                player.attribute -= player.equipment_set.shield.attribute

            player.equipment_set.shield = player_item.item

        player.attribute += player_item.item.attribute

        player_item.amount -= 1

        await ctx.send('equipped')

    @commands.command()
    async def equipped(self, ctx):
        player: Player = session.query(Player).filter(User.discord_id == ctx.author.id).one()

        embed = discord.Embed(
            title='Equipped',
            colour=discord.Colour.random()
        )

        embed.add_field(name='Weapon',
                        value=player.equipment_set.weapon.name if player.equipment_set and player.equipment_set.weapon
                        else "None")

        embed.add_field(name='Shield',
                        value=player.equipment_set.shield.name if player.equipment_set and player.equipment_set.shield
                        else "None")

        await ctx.send(embed=embed)

    @commands.command()
    async def equipments(self, ctx):
        author_id = ctx.author.id

        player = session.query(Player).filter(User.discord_id == author_id).one()

        embed = discord.Embed(
            title='Owned Items',
            colour=discord.Colour.random()
        )

        for player_item in player.items:
            if isinstance(player_item.item, Equipment):
                embed.add_field(
                    name=player_item.item.name,
                    value="+%s" % player_item.amount
                )

        await ctx.send(embed=embed)

    @commands.command()
    async def use(self, ctx, *, arg: str):
        name, amount = strip_name_amount(arg)

        player = session.query(Player).filter(User.discord_id == ctx.author.id).one()

        try:
            player_item: PlayerItem = next(
                player_item for player_item in player.items if
                str(player_item.item.name).lower() == name.lower())
        except StopIteration:
            raise ValueError('Item to use not found')

        if not isinstance(player_item.item, Consumable):
            raise ValueError('cannot apply non-consumable item')

        if player_item.amount < amount:
            raise ValueError('Not enough amount')

        while amount != 0:
            if player_item.item.is_random_attr:
                item_attribute: Attribute = player_item.item.attribute

                # get dict of Attribute's attributes, ignores sqlalchemy instance, and 0 values
                attrs = item_attribute.attrs

                chosen = random.choice(attrs)

                item_value = item_attribute.__getattribute__(chosen)
                player_attr_value = player.__getattribute__(chosen)

                if float(item_value).is_integer():
                    if chosen == 'max_hp':
                        player.max_hp += item_value
                    else:
                        player.__setattr__(chosen, (item_value + player_attr_value))
                else:
                    player.attribute.__setattr__(chosen, round((item_value * player_attr_value) + player_attr_value))
            else:
                # TODO: Add conditional statement that filters percentage over integer
                player.current_hp += player_item.item.attribute.current_hp
                player.max_hp += player_item.item.attribute.max_hp
                player.strength += player_item.item.attribute.strength
                player.defense += player_item.item.attribute.defense

            player_item.amount -= 1
            amount -= 1

        await ctx.send('item is used successfully')


def setup(bot):
    bot.add_cog(ItemCommand(bot))
