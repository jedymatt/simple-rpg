from sqlalchemy import select
from sqlalchemy.orm import joinedload, subqueryload, make_transient

from models import Player, Hostile, Loot, Modifier
from models import User


def get_player(session, discord_id):
    return session.query(Player).options(
        joinedload(Player.user),
        joinedload(Player.attribute),
        joinedload(Player.location)
    ).join(User).filter(User.discord_id == discord_id).one()


def get_hostile(session, hostile_id, make_transient_=False) -> Hostile:
    stmt = select(Hostile).options(
        joinedload(Hostile.attribute),
        joinedload(Hostile.loot).subqueryload(Loot.item_loots)
    ).where(Hostile.id == hostile_id)

    hostile = session.execute(stmt).scalar()

    if make_transient_:
        hostile_make_transient(hostile)
    return hostile


def hostile_make_transient(hostile: Hostile):
    make_transient(hostile)
    make_transient(hostile.attribute)
    make_transient(hostile.loot)


def get_modifier(session, modifier_id):
    stmt = select(Modifier).options(
        joinedload(Modifier.attribute)
    ).where(Modifier.id == modifier_id)

    return session.execute(stmt).scalar()
