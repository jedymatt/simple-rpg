import discord
from discord.ext import commands
from sqlalchemy.sql import func

import models
import models as model
from cogs.utils import stripper
from db.connector import session


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        shop_items = session.query(model.ShopItem).all()

        embed = discord.Embed(
            title='Items for sale',
            colour=discord.Colour.random()
        )

        for shop_item in shop_items:
            shop_item: model.ShopItem = shop_item

            embed.add_field(
                name="%s coins - **%s**" % (shop_item.item.market_value, shop_item.item.name),
                value=shop_item.item.description if shop_item.item.description else '*No description yet*'
            )

        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, *, args):
        name, amount = stripper.strip_name_amount(args)

        # check if valid amount
        if amount <= 0:
            raise ValueError('Amount reached zero or below zero.')

        player: models.Player = session.query(models.Player).filter(models.User.discord_id == ctx.author.id).one()

        # get item in the shop
        item_to_buy: models.Item = session.query(models.Item).filter(
            func.lower(models.Item.name) == name.lower()
        ).one()

        # if item exits then proceed
        if item_to_buy:
            total_cost = item_to_buy.market_value * amount
            # check if player's money is enough
            if player.money < total_cost:
                raise ValueError

            # deduct player's money
            player.money -= total_cost

            # check if queried item to be added is already in the Player.items otherwise create object
            # get item in Player.items
            player_item: models.PlayerItem = next(
                (player_item for player_item in player.items if player_item.item == item_to_buy),
                None
            )
            if player_item:  # if exists
                player_item.amount += amount
            else:  # otherwise does not exists, append object
                player.items.append(
                    models.PlayerItem(
                        item=item_to_buy,
                        amount=amount
                    )
                )

            await ctx.send('Transaction Successful')

        else:  # otherwise raise error
            raise ValueError('Item not found')

    @commands.command()
    async def sell(self, ctx, *, args):
        name, amount = stripper.strip_name_amount(args)

        # check if valid amount
        if amount <= 0:
            raise ValueError('Amount reached zero or below zero.')

        # query Player
        player: models.Player = session.query(models.Player).filter(models.User.discord_id == ctx.author.id).one()

        # search for time that is mentioned by the user
        try:
            item_to_sell: models.PlayerItem = next(
                player_item for player_item in player.items if str(player_item.item.name).lower() == name.lower()
            )
        except StopIteration:
            raise ValueError('Item not found: Cannot sell not owned item.')

        if item_to_sell.amount < amount:  # if lesser than amount mentioned
            raise ValueError('Requested amount exceeds the owned amount')

        item_to_sell.amount -= amount
        player.money += round((amount * item_to_sell.item.market_value) * .80)  # 80% total money gained


def setup(bot: commands.Bot):
    bot.add_cog(Economy(bot))
