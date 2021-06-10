from math import ceil

from cogs.utils.errors import MaximumExpError
from models import Attribute
from models import Character
from models.util import character_next_exp, character_scale_attribute

BASE_EXP = 200
EXP_GROWTH = 1.2
LOOT_GROWTH = 1.4

PLAYER_DATA = {
    "level": 1,
    "exp": 0,
    "money": 500,
    "attribute": {
        "max_hp": 50,
        "strength": 15,
        "defense": 5,
        "growth": 1.4
    },
    "location": "Hometown"
}


def gain_exp(character: Character, exp):
    total_exp = character.exp + exp

    next_exp = character_next_exp(character.level, BASE_EXP, EXP_GROWTH)
    while total_exp >= next_exp:
        print('leveled up')
        raise MaximumExpError('Current Exp reached its maximum to level up')
        # total_exp -= character_next_exp(character.level, BASE_EXP, EXP_GROWTH)
        # character.level += 1
        # character_scale_attribute(character.level, character.attribute)


def combine_attributes(attribute: Attribute, other: Attribute):
    critical_chance = attribute.critical_chance + other.critical_chance
    critical_damage = attribute.critical_damage + other.critical_damage
    evade_chance = attribute.evade_chance + other.evade_chance
    escape_chance = attribute.escape_chance + other.escape_chance

    # restrictions
    if critical_chance > 0.75:
        critical_chance = 0.75
    if critical_damage > 2.00:
        critical_damage = 2.00
    if evade_chance > 0.45:
        evade_chance = 0.45
    if escape_chance > 1.00:
        escape_chance = 1.00

    return Attribute(
        max_hp=attribute.max_hp + other.max_hp,
        strength=attribute.strength + other.strength,
        defense=attribute.defense + other.defense,
        critical_chance=critical_chance,
        critical_damage=critical_damage,
        evade_chance=evade_chance,
        escape_chance=escape_chance,
        growth=attribute.growth + other.growth
    )


def scale_loot(level, loot):
    loot.exp = ceil(loot.exp * (LOOT_GROWTH ** level))
    loot.money = ceil(loot.money * (LOOT_GROWTH ** level))
