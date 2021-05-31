from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, unique=True, nullable=False)
    dice_roll = Column(Integer)

    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'))

    # Relationships
    player = relationship('Player', back_populates='user', uselist=False)

    def __repr__(self):
        return "<User(discord_id='%s', dice_roll='%s', player_id='%s')>" % (
            self.discord_id, self.dice_roll, self.player_id
        )


class Attribute(Base):
    __tablename__ = 'attributes'

    id = Column(Integer, primary_key=True)
    max_hp = Column(Integer)
    strength = Column(Integer)
    defense = Column(Integer)
    critical_chance = Column(Float, default=1)
    critical_damage = Column(Float, default=1)
    evasion = Column(Float, default=1)


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    description = Column(String(250))
    level_requirement = Column(Integer)


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    description = Column(String(250))
    is_tradable = Column(Boolean)
    type = Column(String(50))

    # Foreign Keys
    attribute_id = Column(Integer, ForeignKey('attributes.id'))

    # Relationships
    attribute = relationship('Attribute', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'item',
        'polymorphic_on': type
    }


class Consumable(Item):
    __mapper_args__ = {
        'polymorphic_identity': 'consumable',
        'polymorphic_load': 'selectin'
    }


class Raw(Item):
    __mapper_args__ = {
        'polymorphic_identity': 'raw',
        'polymorphic_load': 'selectin'
    }


class Equipment(Item):
    __mapper_args__ = {
        'polymorphic_identity': 'equipment',
        'polymorphic_load': 'selectin'
    }


class Weapon(Equipment):
    __mapper_args__ = {
        'polymorphic_identity': 'weapon',
        'polymorphic_load': 'inline'
    }


class Shield(Equipment):
    __mapper_args__ = {
        'polymorphic_identity': 'shield',
        'polymorphic_load': 'inline'
    }


class Character(Base):
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True)
    level = Column(Integer)
    exp = Column(Integer)
    type = Column(String(10))

    # Foreign keys
    attribute_id = Column(Integer, ForeignKey('attributes.id'))
    location_id = Column(Integer, ForeignKey('locations.id'))

    # Relationships
    attribute = relationship('Attribute', foreign_keys=[attribute_id], uselist=False)
    location = relationship('Location', foreign_keys=[location_id], uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'character',
        'polymorphic_on': type
    }


class Player(Character):
    __tablename__ = 'players'

    id = Column(Integer, ForeignKey('characters.id'), primary_key=True)
    money = Column(Integer)

    # Foreign keys
    equipment_set_id = Column(Integer, ForeignKey('equipment_sets.id'))

    # relationships
    user = relationship('User', back_populates='player', uselist=False)
    items = relationship('PlayerItem', uselist=True)
    equipment_set = relationship('EquipmentSet', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'player',
        'polymorphic_load': 'selectin'
    }

    def __repr__(self):
        return "<Player(level='%s', exp='%s', money='%s')>" % (
            self.level, self.exp, self.money
        )


class PlayerItem(Base):
    __tablename__ = 'player_items'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    amount = Column(Integer)

    item = relationship('Item', uselist=False)


class EquipmentSet(Base):
    __tablename__ = 'equipment_sets'

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    weapon_id = Column(Integer, ForeignKey('items.id'))
    shield_id = Column(Integer, ForeignKey('items.id'))

    # Relationships
    weapon = relationship('Weapon', foreign_keys=[weapon_id], uselist=False)
    shield = relationship('Shield', foreign_keys=[shield_id], uselist=False)


class Hostile(Character):
    __tablename__ = 'hostiles'

    id = Column(Integer, ForeignKey('characters.id'), primary_key=True)
    name = Column(String(50), unique=True)

    # Foreign keys
    drop_loot_id = Column(Integer, ForeignKey('loots.id'))

    # Relationships
    drop_loot = relationship('Loot', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'hostile',
        'polymorphic_load': 'selectin'
    }


class Loot(Base):
    __tablename__ = 'loots'

    id = Column(Integer, primary_key=True)
    exp = Column(Integer)
    money = Column(Integer)

    # relationships
    item_loots = relationship('ItemLoot')


class ItemLoot(Base):
    __tablename__ = 'item_loots'

    id = Column(Integer, primary_key=True)
    min = Column(Integer)
    max = Column(Integer)
    drop_chance = Column(Float)

    # Foreign Keys
    item_id = Column(Integer, ForeignKey('items.id'))
    loot_id = Column(Integer, ForeignKey('loots.id'))

    # Relationships
    item = relationship('Item', uselist=False)


class LocationLoot(Base):
    __tablename__ = 'location_loots'

    id = Column(Integer, primary_key=True)

    # foreign keys
    location_id = Column(Integer, ForeignKey('locations.id'))
    loot_id = Column(Integer, ForeignKey('loots.id'))

    # relationships
    location = relationship('Location', uselist=False)
    loot = relationship('Loot', uselist=False)


class Blueprint(Base):
    __tablename__ = 'blueprints'

    id = Column(Integer, primary_key=True)

    # Foreign keys
    item_id = Column(Integer, ForeignKey('items.id'))

    # relationships
    item = relationship('Item', uselist=False)
    blueprint_materials = relationship('BlueprintMaterial', back_populates='blueprint')


class BlueprintMaterial(Base):
    __tablename__ = 'blueprint_materials'

    id = Column(Integer, primary_key=True)

    # Foreign keys
    item_id = Column(Integer, ForeignKey('items.id'))
    blueprint_id = Column(Integer, ForeignKey('blueprints.id'))

    # Relationships
    item = relationship('Item', uselist=False)
    blueprint = relationship('Blueprint', back_populates='blueprint_materials', uselist=False)


class Shop(Base):
    __tablename__ = 'shop'

    id = Column(Integer, primary_key=True)
    value = Column(Integer)

    # foreign keys
    item_id = Column(Integer, ForeignKey('items.id'))

    # relationships
    item = relationship('Item', uselist=False)
