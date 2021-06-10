from math import ceil
from math import floor
from random import random

from models import Attribute


def character_next_exp(current_level, base_exp, exp_growth):
    return floor(base_exp * (current_level ** exp_growth))


def character_total_exp(current_level, base_exp, exp_growth):
    total_exp = 0
    level = 1

    while level <= current_level:
        total_exp += character_next_exp(level, base_exp, exp_growth)
        level += 1

    return total_exp


def character_level_from_total_exp(total_exp, base_exp, exp_growth):
    level = 1

    while total_exp > character_total_exp(level, base_exp, exp_growth):
        level += 1

    return level


def character_scale_attribute(level, attribute: Attribute):
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



