from collections import namedtuple
from math import ceil
from math import floor
from random import random

from cogs.utils.errors import ExpRequirementNotReached
from cogs.utils.player import PLAYER_INITIAL_DATA
from models import Attribute
from models import Character
from models import Hostile
from models import Modifier

BASE_EXP = 200
EXP_GROWTH = 1.2
LOOT_GROWTH = 1.4

MAX_CRITICAL_CHANCE = 0.75
MAX_CRITICAL_DAMAGE = 2.00
MAX_EVADE_CHANCE = 0.45
MAX_ESCAPE_CHANCE = 1

NameAmount = namedtuple("NameAmount", ["name", "amount"])


def combine_attributes(attribute: Attribute, other: Attribute):
    critical_chance = attribute.critical_chance + other.critical_chance
    critical_damage = attribute.critical_damage + other.critical_damage
    evade_chance = attribute.evade_chance + other.evade_chance
    escape_chance = attribute.escape_chance + other.escape_chance

    # restrictions
    if critical_chance > MAX_CRITICAL_CHANCE:
        critical_chance = MAX_CRITICAL_CHANCE
    if critical_damage > MAX_CRITICAL_DAMAGE:
        critical_damage = MAX_CRITICAL_DAMAGE
    if evade_chance > MAX_EVADE_CHANCE:
        evade_chance = MAX_EVADE_CHANCE
    if escape_chance > MAX_ESCAPE_CHANCE:
        escape_chance = MAX_ESCAPE_CHANCE

    attribute.max_hp += other.max_hp
    attribute.strength += other.strength
    attribute.defense += other.defense
    attribute.critical_chance = critical_chance
    attribute.critical_damage = critical_damage
    attribute.evade_chance = evade_chance
    attribute.escape_chance = escape_chance
    attribute.growth += other.growth

    return attribute


def scale_loot(level, loot):
    loot.exp = ceil(loot.exp * (LOOT_GROWTH ** level))
    loot.money = ceil(loot.money * (LOOT_GROWTH ** level))


def adjust_hostile_enemy(new_level: int, hostile: Hostile, modifier: Modifier = None):
    """

    Adjust hostile enemy's attribute with modifier, if not None, and loot according to its new level

    Args:
        new_level:
        hostile:
        modifier:
    """
    hostile.level = new_level
    if modifier:
        hostile.name = f"{modifier.prefix} {hostile.name}"
        combine_attributes(hostile.attribute, modifier.attribute)
        hostile.loot.exp = ceil(hostile.loot.exp * (1 + modifier.bonus_exp))
        hostile.loot.money = ceil(hostile.loot.money * (1 + modifier.bonus_money))

    scale_attribute(hostile.level, hostile.attribute)
    scale_loot(hostile.level, hostile.loot)


class BattleSimulator:

    def __init__(self, character: Character, opponent: Character):
        self.character = character
        self.opponent = opponent

        self.character_record = BattleRecord(character)
        self.opponent_record = BattleRecord(opponent)
        self.rounds_count = 0

    def start(self):
        character_hp = self.character.attribute.max_hp
        opponent_hp = self.opponent.attribute.max_hp
        character_turn = True
        while character_hp > 0 and opponent_hp > 0:

            if character_turn:
                opponent_hp = self.attack(
                    opponent_hp,
                    self.character.attribute,
                    self.character_record,
                    self.opponent.attribute,
                    self.opponent_record
                )

                if self.opponent_record.has_escaped:
                    break

                character_turn = False
                self.rounds_count += 1
            else:
                character_hp = self.attack(
                    character_hp,
                    self.opponent.attribute,
                    self.opponent_record,
                    self.character.attribute,
                    self.character_record
                )

                if self.character_record.has_escaped:
                    break

                character_turn = True

        if self.character_record.has_escaped or self.opponent_record.has_escaped:
            return None

        return self.character if character_hp > 0 else self.opponent

    @staticmethod
    def attack(opponent_hp, attacker_attribute, character_record, opponent_attribute, opponent_record):

        if random_boolean(opponent_attribute.evade_chance):
            opponent_record.evaded_hits += 1
            return opponent_hp

        damage_dealt = calculate_damage(attacker_attribute, opponent_attribute)

        # escape condition (escape when in grave danger)
        if damage_dealt[0] >= opponent_hp:
            if random_boolean(opponent_attribute.escape_chance):
                opponent_record.has_escaped = True
                return opponent_hp

        opponent_hp -= damage_dealt[0]

        # character record battle
        character_record.total_hits += 1
        character_record.total_damage_dealt += damage_dealt[0]
        if damage_dealt[0] > character_record.highest_damage:
            character_record.highest_damage = damage_dealt[0]
            # if the damage dealt is critical hit
            if damage_dealt[1]:
                character_record.highest_damage_is_crit = True
            else:
                character_record.highest_damage_is_crit = False
        character_record.crit_hits += 1 if damage_dealt[1] else 0

        # opponent record
        opponent_record.total_damage_received += damage_dealt[0]
        if opponent_record.lowest_damage_received == 0:
            opponent_record.lowest_damage_received = damage_dealt[0]
        elif damage_dealt[0] < opponent_record.lowest_damage_received:
            opponent_record.lowest_damage_received = damage_dealt[0]
        opponent_record.total_hits_received += 1
        opponent_record.current_hp = opponent_hp
        return opponent_hp


class BattleRecord:
    def __init__(self, character: Character):
        self.current_hp = character.attribute.max_hp
        self.total_damage_dealt = 0
        self.highest_damage = 0
        self.highest_damage_is_crit = False
        self.crit_hits = 0
        self.total_damage_received = 0
        self.lowest_damage_received = 0
        self.evaded_hits = 0
        self.has_escaped = False
        self.total_hits = 0
        self.total_hits_received = 0

    def average_damage_received(self):
        if self.total_hits_received == 0:
            return 0

        return round(self.total_damage_received / self.total_hits_received, 1)

    def average_damage_dealt(self):
        if self.total_hits == 0:
            return 0

        return round(self.total_damage_dealt / self.total_hits, 1)


def next_exp(current_level):
    return floor(BASE_EXP * (current_level ** EXP_GROWTH))


def total_exp_from_level(current_level):
    total_exp = 0
    level = 1

    while level <= current_level:
        total_exp += next_exp(level)
        level += 1

    return total_exp


def level_from_total_exp(total_exp):
    level = 1

    while total_exp > total_exp_from_level(level):
        level += 1

    return level


def scale_attribute(level, attribute: Attribute):
    attribute.max_hp = floor(attribute.max_hp * (attribute.growth ** (level - 1)))
    attribute.strength = floor(attribute.strength * (attribute.growth ** (level - 1)))
    attribute.defense = floor(attribute.defense * (attribute.growth ** (level - 1)))


def player_changed_attribute(current_level, new_level):
    attribute = Attribute()

    attribute.max_hp = floor(
        PLAYER_INITIAL_DATA['attribute']['max_hp'] * (PLAYER_INITIAL_DATA['attribute']['growth'] ** (new_level - 1)))
    attribute.max_hp -= floor(PLAYER_INITIAL_DATA['attribute']['max_hp'] * (
        PLAYER_INITIAL_DATA['attribute']['growth'] ** (current_level - 1)))

    attribute.strength = floor(
        PLAYER_INITIAL_DATA['attribute']['strength'] * (PLAYER_INITIAL_DATA['attribute']['growth'] ** (new_level - 1)))
    attribute.strength -= floor(PLAYER_INITIAL_DATA['attribute']['strength'] * (
        PLAYER_INITIAL_DATA['attribute']['growth'] ** (current_level - 1)))

    attribute.defense = floor(
        PLAYER_INITIAL_DATA['attribute']['defense'] * (PLAYER_INITIAL_DATA['attribute']['growth'] ** (new_level - 1)))
    attribute.defense -= floor(PLAYER_INITIAL_DATA['attribute']['defense'] * (
        PLAYER_INITIAL_DATA['attribute']['growth'] ** (current_level - 1)))

    return attribute


def random_boolean(chance: float):
    return random() <= chance


def calculate_damage(attacker: Attribute, receiver: Attribute):
    is_critical_hit = random_boolean(attacker.critical_chance)

    damage_taken = (attacker.strength ** 2) / (attacker.strength + receiver.defense)

    if is_critical_hit:
        damage_taken *= (1 + attacker.critical_damage)

    return ceil(damage_taken), is_critical_hit


def level_up(character: Character):
    if character.exp < next_exp(character.level):
        raise ExpRequirementNotReached('Exp not enough to level up')

    level_gained = 0
    while character.exp >= next_exp(character.level + level_gained):
        level_gained += 1

    character.level += level_gained
    character.exp = next_exp(character.level) - character.exp

    return level_gained
