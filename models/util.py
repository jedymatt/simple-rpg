from math import floor
from random import random


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


def scale_stats(level, hp, strength, defense, stat_growth):
    level -= 1

    new_hp = floor(hp * (stat_growth ** level))
    new_strength = floor(strength * (stat_growth ** level))
    new_defense = floor(defense * (stat_growth ** level))

    return [new_hp, new_strength, new_defense]


def random_boolean(chance: float):
    return random() <= chance
