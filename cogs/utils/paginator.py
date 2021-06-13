import discord
from discord import Embed
from discord.ext import menus
from discord.ext.menus import MenuPages

from cogs.utils import images
from cogs.utils.character import BattleRecord
from models import Character


class EmbedListPage(menus.ListPageSource):

    def __init__(self, global_message: str, embeds, *, per_page=1, footer_counter=True):
        super().__init__(embeds, per_page=per_page)
        self.global_message = global_message
        self.footer_counter = footer_counter

    async def format_page(self, menu: MenuPages, page):
        if self.footer_counter:
            page.set_footer(text=f"Simple RPG | Page {menu.current_page + 1} of {self.get_max_pages()}")

        return {'content': self.global_message, 'embed': page}


def record_embed(title, name, character: Character, record: BattleRecord, thumbnail_url=None):
    colour = discord.Colour.green() if record.current_hp > 0 else discord.Colour.red()

    embed = Embed(
        title=title,
        colour=colour
    )

    embed.set_thumbnail(url=thumbnail_url if thumbnail_url else images.DEFAULT)

    values = [
        ('Lvl.{} {}', [character.level, name]),
        ('Hp: {}/{}', [record.current_hp if record.current_hp > 0 else 0, character.attribute.max_hp]),
        ('Ave. Dmg/Hit: {}', [record.average_damage_dealt()]),
        ('Highest Dmg: {}{}', [record.highest_damage, '[crit]' if record.highest_damage_is_crit else '']),
        ('Crit Hits: {}', [record.crit_hits]),
        ('Evaded Hits: {}', [record.evaded_hits]),
        ('Low. Dmg Received: {}', [record.lowest_damage_received])
    ]

    value = '\n'.join(value[0].format(*value[1]) for value in values)

    embed.description = value

    return embed


class Confirm(menus.Menu):
    def __init__(self, msg):
        super().__init__(timeout=30.0, delete_message_after=True)
        self.msg = msg
        self.result = None

    async def send_initial_message(self, ctx, channel):
        return await channel.send(self.msg)

    @menus.button('\N{WHITE HEAVY CHECK MARK}')
    async def do_confirm(self, payload):
        self.result = True
        self.stop()

    @menus.button('\N{CROSS MARK}')
    async def do_deny(self, payload):
        self.result = False
        self.stop()

    async def prompt(self, ctx):
        await self.start(ctx, wait=True)
        return self.result
