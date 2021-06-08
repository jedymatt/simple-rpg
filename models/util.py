from math import ceil
from math import floor
from random import random

from models import Attribute


def player_next_exp(current_level, base_exp, exp_growth):
    return floor(base_exp * (current_level ** exp_growth))


def player_total_exp(current_level, base_exp, exp_growth):
    total_exp = 0
    level = 1

    while level <= current_level:
        total_exp += player_next_exp(level, base_exp, exp_growth)
        level += 1

    return total_exp


def player_level_from_total_exp(total_exp, base_exp, exp_growth):
    level = 1

    while total_exp > player_total_exp(level, base_exp, exp_growth):
        level += 1

    return level


def scale_attribute(level, attribute: Attribute):
    attribute.max_hp = floor(attribute.max_hp * (attribute.growth ** (level - 1)))
    attribute.strength = floor(attribute.strength * (attribute.growth ** (level - 1)))
    attribute.defense = floor(attribute.defense * (attribute.growth ** (level - 1)))


def random_boolean(chance: float):
    return random() <= chance


def calculate_damage(attacker: Attribute, receiver: Attribute):
    is_critical_hit = random_boolean(attacker.critical_chance)

    damage_taken = (attacker.strength ** 2) / (attacker.strength + receiver.defense)

    if is_critical_hit:
        damage_taken *= (1 + attacker.critical_damage)

    return ceil(damage_taken), is_critical_hit


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
