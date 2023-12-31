import json

from db.connector import session
from models import Item, Location, Loot, ItemLoot, LocationLoot


# seed Location and Items first before executing this code
def load_location_loots():
    with open('location_loots.json') as _json_file:
        location_loots = []
        for location_loot in json.load(_json_file):
            location_loots.append(
                LocationLoot(
                    location=session.query(Location).filter(Location.name == location_loot['location']).one(),

                    loot=Loot(
                        exp=location_loot['loot']['exp'],
                        money=location_loot['loot']['money'],
                        item_loots=[
                            ItemLoot(
                                min=item['min'],
                                max=item['max'],
                                item=session.query(Item).filter(Item.name == item['item']).one(),
                                drop_chance=item['drop_chance']
                            ) for item in location_loot['loot']['item_loots']
                        ]
                    )
                )
            )
    return location_loots
# session.add_all(location_loots)
# session.commit()
