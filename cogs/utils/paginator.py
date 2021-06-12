import discord
from discord import Embed, Message
from discord.ext import menus
from discord.ext.menus import MenuPages, Menu

from cogs.utils.character import BattleRecord
from models import Character


class ListPage(menus.ListPageSource):

    def __init__(self, entries, *, per_page=1):
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: Menu, page):
        return page


def character_hunt_record(title, name, character: Character, record: BattleRecord):
    colour = discord.Colour.green() if record.current_hp > 0 else discord.Colour.red()

    embed = Embed(
        title=title,
        colour=colour
    )

    str_value = "HP: {} / {}\nAve. Dmg/hit: {}\nHighest Dmg: {}{}\nCrit Hit(s): {}\nEvaded Hit(s): {}\nLowest Damage " \
                "Received: {}".format(record.current_hp if record.current_hp > 0 else 0,
                                      character.attribute.max_hp,
                                      round(record.total_damage_dealt / record.total_hits,
                                            1),
                                      record.highest_damage,
                                      '[Critical]' if record.highest_damage_is_crit else '',
                                      record.crit_hits,
                                      record.evaded_hits,
                                      record.lowest_damage_received)

    embed.add_field(
        name=f"Lvl.{character.level} {name}",
        value=str_value
    )

    return embed


class EmbedPages(menus.Menu):

    def __init__(self, msg, embeds):
        super().__init__()
        self.timeout = 30
        self.msg = msg
        self.embeds = embeds
        self.current_page = 0
        self.max_pages = len(embeds)

    async def send_initial_message(self, ctx, channel):
        return await channel.send(content=self.msg, embed=self.embeds[self.current_page])

    @menus.button("\N{Black Left-Pointing Triangle}")
    async def on_backward(self, payload):
        if self.current_page <= 0:
            pass
        self.current_page -= 1
        await self.message.edit(embed=self.embeds[self.current_page])

    @menus.button("\N{Black Right-Pointing Triangle}")
    async def on_forward(self, payload):
        if self.current_page >= self.max_pages - 1:
            pass
        self.current_page += 1
        await self.message.edit(embed=self.embeds[self.current_page])
