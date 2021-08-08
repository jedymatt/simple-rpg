from sqlalchemy import BigInteger
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declared_attr
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, unique=True, nullable=False)

    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'))

    # Relationships
    player = relationship('Player', back_populates='user', uselist=False)

    def __repr__(self):
        return "<User(discord_id='%s', player_id='%s')>" % (
            self.discord_id, self.player_id
        )


class Attribute(Base):
    __tablename__ = 'attributes'

    id = Column(Integer, primary_key=True)
    max_hp = Column(Integer, default=0)
    strength = Column(Integer, default=0)
    defense = Column(Integer, default=0)
    critical_chance = Column(Float, default=0)
    critical_damage = Column(Float, default=0)
    evade_chance = Column(Float, default=0)
    escape_chance = Column(Float, default=0)
    growth = Column(Float, default=0)

    def __repr__(self):
        return "<Attribute(max_hp='%s', strength='%s', defense='%s', critical_chance='%s', critical_damage='%s', " \
               "evade_chance='%s', growth='%s')>" % (
                   self.max_hp, self.strength, self.defense, self.critical_chance, self.critical_damage,
                   self.evade_chance, self.growth
               )


class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    description = Column(String(250))
    level_requirement = Column(Integer)

    def __repr__(self):
        return "<Location(name='%s', description='%s', level_requirement='%s')>" % (
            self.name, self.description, self.level_requirement
        )


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

    def __repr__(self):
        return "<Item(name='%s', description='%s', is_tradable='%s', type='%s')>" % (
            self.name, self.description, self.is_tradable, self.type
        )


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

    def __repr__(self):
        return super().__repr__()


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


class Armour(Equipment):
    __mapper_args__ = {
        'polymorphic_identity': 'armour',
        'polymorphic_load': 'inline'
    }


# Abstract class
class Character(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)
    level = Column(Integer)
    exp = Column(Integer)

    # Foreign keys
    @declared_attr
    def attribute_id(cls):
        return Column(Integer, ForeignKey('attributes.id'))

    @declared_attr
    def location_id(cls):
        return Column(Integer, ForeignKey('locations.id'))

    # Relationships
    @declared_attr
    def attribute(cls):
        return relationship('Attribute', foreign_keys=[cls.attribute_id], uselist=False)

    @declared_attr
    def location(cls):
        return relationship('Location', foreign_keys=[cls.location_id], uselist=False)


class Player(Character):
    __tablename__ = 'players'

    # id = Column(Integer, ForeignKey('characters.id'), primary_key=True)
    money = Column(Integer)

    # Foreign keys
    equipment_slot = Column(Integer, ForeignKey('equipment_slots.id'))

    # relationships
    user = relationship('User', back_populates='player', uselist=False)
    items = relationship('PlayerItem', uselist=True)
    equipment_set = relationship('EquipmentSlot', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'players'
    }

    def __repr__(self):
        return "<Player(level='%s', exp='%s', money='%s')>" % (
            self.level, self.exp, self.money
        )


class Hostile(Character):
    __tablename__ = 'hostiles'

    # id = Column(Integer, ForeignKey('characters.id'), primary_key=True)
    name = Column(String(50), unique=True)

    # Foreign keys
    loot_id = Column(Integer, ForeignKey('loots.id'))

    # Relationships
    loot = relationship('Loot', uselist=False)

    __mapper_args__ = {
        'polymorphic_identity': 'hostiles'
    }

    def __repr__(self):
        return "<Hostile(name='%s', level='%s', exp='%s'>" % (
            self.name, self.level, self.exp
        )


class PlayerItem(Base):
    __tablename__ = 'player_items'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    amount = Column(Integer)

    item = relationship('Item', uselist=False)

    def __repr__(self):
        return "<PlayerItem(amount='%s')>" % (
            self.amount
        )


class EquipmentSlot(Base):
    __tablename__ = 'equipment_slots'

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    weapon_id = Column(Integer, ForeignKey('items.id'))
    armour_id = Column(Integer, ForeignKey('items.id'))

    # Relationships
    weapon = relationship('Weapon', foreign_keys=[weapon_id], uselist=False)
    armour = relationship('Armour', foreign_keys=[armour_id], uselist=False)


class Modifier(Base):
    __tablename__ = 'modifiers'

    id = Column(Integer, primary_key=True)
    prefix = Column(String(10), unique=True)
    bonus_exp = Column(Float)
    bonus_money = Column(Float)

    # Foreign keys
    attribute_id = Column(Integer, ForeignKey('attributes.id'))

    # relationships
    attribute = relationship('Attribute', uselist=False)


class Loot(Base):
    __tablename__ = 'loots'

    id = Column(Integer, primary_key=True)
    exp = Column(Integer)
    money = Column(Integer)

    # relationships
    item_loots = relationship('ItemLoot', back_populates='loot')

    def __repr__(self):
        return "<Loot(exp='%s', money='%s')>" % (
            self.exp, self.money
        )


class ItemLoot(Base):
    __tablename__ = 'item_loots'

    id = Column(Integer, primary_key=True)
    min = Column(Integer, default=1)
    max = Column(Integer, default=1)
    drop_chance = Column(Float)

    # Foreign Keys
    item_id = Column(Integer, ForeignKey('items.id'))
    loot_id = Column(Integer, ForeignKey('loots.id'))

    # Relationships
    item = relationship('Item', uselist=False)
    loot = relationship('Loot', back_populates='item_loots', uselist=False)

    def __repr__(self):
        return "<ItemLoot(drop_chance='%s')>" % (
            self.drop_chance
        )


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
    blueprint_materials = relationship(
        'BlueprintMaterial', back_populates='blueprint')


class BlueprintMaterial(Base):
    __tablename__ = 'blueprint_materials'

    id = Column(Integer, primary_key=True)

    # Foreign keys
    item_id = Column(Integer, ForeignKey('items.id'))
    blueprint_id = Column(Integer, ForeignKey('blueprints.id'))

    # Relationships
    item = relationship('Item', uselist=False)
    blueprint = relationship(
        'Blueprint', back_populates='blueprint_materials', uselist=False)


class Shop(Base):
    __tablename__ = 'shop'

    id = Column(Integer, primary_key=True)
    value = Column(Integer)

    # foreign keys
    item_id = Column(Integer, ForeignKey('items.id'))

    # relationships
    item = relationship('Item', uselist=False)


class Boss(Base):
    __tablename__ = 'bosses'

    id = Column(Integer, primary_key=True)
    level_requirement = Column(Integer)
    type = Column(String(10))

    hostile_id = Column(Integer, ForeignKey('hostiles.id'))

    hostile = relationship('Hostile')

    __mapper_args__ = {
        'polymorphic_identity': 'boss',
        'polymorphic_on': type
    }


class EliteBoss(Boss):
    __mapper_args__ = {
        'polymorphic_identity': 'elite',
        'polymorphic_load': 'selectin'
    }


class WorldBoss(Boss):
    __mapper_args__ = {
        'polymorphic_identity': 'world',
        'polymorphic_load': 'selectin'
    }
