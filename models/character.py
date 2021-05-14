import random
from datetime import datetime, timezone
from math import floor, ceil

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Float
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from .base import Attribute, Base
from .util import occurrence

from .util import random_boolean

HP_REGEN_AMOUNT = 10
HP_REGEN_INTERVAL = 600  # 10 MINUTES

player_base_stats = {
    'hp': 50,
    'strength': 15,
    'defense': 5,
}


class Character(Base):
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    stat_growth = Column(Float)
    type = Column(String(50))
    attribute_id = Column(ForeignKey('attributes.id'))
    location_id = Column(ForeignKey('locations.id'))

    attribute = relationship('Attribute', foreign_keys=[attribute_id], uselist=False)
    location = relationship('Location', foreign_keys=[location_id], uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'character',
        'polymorphic_on': type
    }

    def take_damage(self, opponent_strength):
        """
        Take damage, with 20% chance to deal additional 20% to 40% damage

        :rtype: int
        :param opponent_strength: Character.strength or Attribute.strength
        :return: damage taken
        """
        # damage = (attacker's strength ^ 2) / (attacker's strength + target defense)
        critical_rate = 0.20  # 20%
        critical_damage_min = 1.25  # 25% damage
        critical_damage_max = 1.40  # 40% damage

        # if critical hit occurs
        if random_boolean(critical_rate):
            critical_damage = round(random.uniform(critical_damage_min, critical_damage_max), 2)

            damage_taken = ceil(((opponent_strength ** 2) / (opponent_strength + self.defense)) * critical_damage)
        else:
            damage_taken = ceil((opponent_strength ** 2) / (opponent_strength + self.defense))

        self.current_hp -= damage_taken

        if self.current_hp < 0:
            self.current_hp = 0

        return damage_taken

    @hybrid_property
    def current_hp(self):
        if self.attribute:
            return self.attribute.current_hp
        else:
            return None

    @current_hp.setter
    def current_hp(self, value):
        if not self.attribute:
            self.attribute = Attribute()
        self.attribute.current_hp = value

    @hybrid_property
    def max_hp(self):
        if self.attribute:
            return self.attribute.max_hp
        else:
            return None

    @max_hp.setter
    def max_hp(self, value):
        if not self.attribute:
            self.attribute = Attribute()
        self.attribute.max_hp = value

    @hybrid_property
    def strength(self):
        if self.attribute:
            return self.attribute.strength
        else:
            return None

    @strength.setter
    def strength(self, value):
        if not self.attribute:
            self.attribute = Attribute()
        self.attribute.strength = value

    @hybrid_property
    def defense(self):
        if self.attribute:
            return self.attribute.defense
        else:
            return None

    @defense.setter
    def defense(self, value):
        if not self.attribute:
            self.attribute = Attribute()
        self.attribute.defense = value

    def __repr__(self):
        return "<Character(level='%s', exp='%s', type='%s')>" % (
            self.level,
            self.exp,
            self.type
        )


class PlayerItem(Base):
    __tablename__ = 'player_items'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('characters.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    amount = Column(Integer)

    item = relationship('Item', uselist=False)


class Player(Character):
    __tablename__ = 'players'

    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)

        # set Player default values
        self.base_hp = player_base_stats['hp']
        self.base_strength = player_base_stats['strength']
        self.base_defense = player_base_stats['defense']

    user_id = Column(Integer, ForeignKey('users.id'))
    money = Column(Integer, default=0)
    hp_last_updated = Column(DateTime(timezone=True), default=func.utcnow())

    user = relationship('User', back_populates='player', uselist=False)
    items: list = relationship('PlayerItem')
    equipment_set = relationship('EquipmentSet', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'player',
        'polymorphic_load': 'selectin'
    }

    def is_full_hp(self):
        return self.current_hp == self.max_hp

    @hybrid_property
    def current_hp(self):
        if self.attribute.current_hp and self.max_hp:  # if max hp is not None

            if self.attribute.current_hp < self.max_hp:

                regen = occurrence(self.hp_last_updated, HP_REGEN_INTERVAL) * HP_REGEN_AMOUNT
                self.attribute.current_hp += regen

                if self.attribute.current_hp > self.max_hp:  # if current hp exceeds the max hp
                    self.attribute.current_hp = self.max_hp  # set the current hp value as max hp

        return self.attribute.current_hp

    @current_hp.setter
    def current_hp(self, value):
        if self.max_hp:  # if max hp is not None
            if value > self.max_hp:
                raise ValueError('Value exceeds the max_hp')

            if self.is_full_hp():  # condition first if value is full hp
                self.hp_last_updated = datetime.now(timezone.utc)

        self.attribute.current_hp = value

    @hybrid_property
    def max_hp(self):
        return self.attribute.max_hp

    @max_hp.setter
    def max_hp(self, value):
        self.attribute.max_hp = value
        self.hp_last_updated = datetime.now(timezone.utc)

    def next_level_exp(self):
        base_exp = 200
        return floor(base_exp * (self.level ** 1.2))

    def level_up(self):

        # get stat to be added by getting the differences
        gap_str = floor(self.base_strength * (self.stat_growth ** (self.level + 1))) - floor(
            self.base_strength * (self.stat_growth ** self.level))
        gap_def = floor(self.base_defense * (self.stat_growth ** (self.level + 1))) - floor(
            self.base_defense * (self.stat_growth ** self.level))

        self.strength += gap_str
        self.defense += gap_def

        self.level += 1

    # FIXME: fix level up only once
    def add_exp(self, value):
        if value < 0:
            raise ValueError('value is lesser or equal zero')

        self.exp += value
        if self.exp >= self.next_level_exp():
            self.exp -= self.next_level_exp()
            self.level_up()

    def reduce_exp(self, value):
        if value < 0:
            raise ValueError('Cannot reduce from a negative value')

        self.exp -= value
        if self.exp < 0:
            self.level -= 1
            self.exp = (self.next_level_exp() + self.exp)
            # TODO: reduce base stats


class EquipmentSet(Base):
    __tablename__ = 'equipment_sets'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('characters.id'))
    weapon_id = Column(Integer, ForeignKey('items.id'))
    shield_id = Column(Integer, ForeignKey('items.id'))

    weapon = relationship('Weapon', uselist=False, foreign_keys=[weapon_id])
    shield = relationship('Shield', uselist=False, foreign_keys=[shield_id])

    def __repr__(self):
        return "EquipmentSet(weapon='%s', shield='%s')" % (self.weapon.name, self.shield.name)


class Hostile(Character):
    # add loot reward
    loot_id = Column(Integer, ForeignKey('loots.id'))
    loot = relationship('Loot', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'hostile',
        'polymorphic_load': 'inline'
    }
