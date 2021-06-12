from math import ceil

from cogs.utils.errors import MaximumExpError
from models import Attribute
from models import Character
from models import Hostile
from models import Item
from models import Modifier
from models import Player
from models import PlayerItem
from models.util import character_next_exp, character_scale_attribute, calculate_damage, random_boolean

BASE_EXP = 200
EXP_GROWTH = 1.2
LOOT_GROWTH = 1.4

MAX_CRITICAL_CHANCE = 0.75
MAX_CRITICAL_DAMAGE = 2.00
MAX_EVADE_CHANCE = 0.45
MAX_ESCAPE_CHANCE = 1

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

    # return Attribute(
    #     max_hp=attribute.max_hp + other.max_hp,
    #     strength=attribute.strength + other.strength,
    #     defense=attribute.defense + other.defense,
    #     critical_chance=critical_chance,
    #     critical_damage=critical_damage,
    #     evade_chance=evade_chance,
    #     escape_chance=escape_chance,
    #     growth=attribute.growth + other.growth
    # )


def scale_loot(level, loot):
    loot.exp = ceil(loot.exp * (LOOT_GROWTH ** level))
    loot.money = ceil(loot.money * (LOOT_GROWTH ** level))


def add_player_item(player: Player, item: Item, amount: int):
    # scan if item exists in Player.items
    player_item = next(
        (player_item for player_item in player.items if player_item.item.name == item.name),
        None
    )
    if player_item:
        player_item.amount += amount
    else:
        player.items.append(
            PlayerItem(
                item=item,
                amount=amount
            )
        )


def create_hostile_enemy(target_level: int, hostile: Hostile, modifier: Modifier = None):
    hostile.level = target_level
    if modifier:
        hostile.name = f"{modifier.prefix} {hostile.name}"
        combine_attributes(hostile.attribute, modifier.attribute)
        hostile.loot.exp = ceil(hostile.loot.exp * (1 + modifier.bonus_exp))
        hostile.loot.money = ceil(hostile.loot.money * (1 + modifier.bonus_money))

    character_scale_attribute(hostile.level, hostile.attribute)
    scale_loot(hostile.level, hostile.loot)
    return hostile


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

        opponent_record.current_hp = opponent_hp
        return opponent_hp


class BattleRecord:
    def __init__(self, character: Character):
        self.current_hp = character.attribute.max_hp
        self.total_damage_dealt = 0
        self.average_damage_dealt = 0
        self.highest_damage = 0
        self.highest_damage_is_crit = False
        self.crit_hits = 0
        self.total_damage_received = 0
        self.average_damage_received = 0
        self.lowest_damage_received = 0
        self.evaded_hits = 0
        self.has_escaped = False
        self.total_hits = 0
