from math import floor

from models import PlayerItem, Item

PLAYER_INITIAL_DATA = {
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


def add_item(player_items: list[PlayerItem], item: Item, amount: int):
    # get the item that exists in player_items
    player_item = next(
        (player_item for player_item in player_items if player_item.item.name == item.name),
        None
    )

    if player_item:
        player_item.amount += amount
    else:
        player_items.append(
            PlayerItem(
                item=item,
                amount=amount
            )
        )


def player_scale_attribute(level, attribute):
    attribute.max_hp = floor(
        PLAYER_INITIAL_DATA['attribute']['max_hp'] * (PLAYER_INITIAL_DATA['attribute']['growth'] ** (level - 1))
    )

    attribute.strength = floor(
        PLAYER_INITIAL_DATA['attribute']['strength'] * (PLAYER_INITIAL_DATA['attribute']['growth'] ** (level - 1)))

    attribute.defense = floor(
        PLAYER_INITIAL_DATA['attribute']['defense'] * (PLAYER_INITIAL_DATA['attribute']['growth'] ** (level - 1)))
