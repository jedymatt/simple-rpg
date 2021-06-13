import json

from db.connector import session
from models import Attribute, ItemLoot, Loot, Raw, Location, Hostile


# seed locations and items before executing this code
def load_hostiles():
    with open('hostiles.json') as _json_file:
        hostiles = []
        for hostile in json.load(_json_file):
            hostiles.append(
                Hostile(
                    name=hostile['name'],
                    level=hostile['level'],
                    exp=hostile['exp'],
                    attribute=Attribute(
                        **hostile['attribute']
                    ),
                    location=session.query(Location).filter(Location.name == hostile['location']).one(),
                    loot=Loot(
                        exp=hostile['loot']['exp'],
                        money=hostile['loot']['money'],
                        item_loots=[
                            ItemLoot(
                                drop_chance=item_loot['drop_chance'],
                                item=session.query(Raw).filter(Raw.name == item_loot['item']).one()
                            ) for item_loot in hostile['loot']['item_loots']
                        ]
                    )
                )
            )
    return hostiles
# session.add_all(hostiles)
# session.commit()
