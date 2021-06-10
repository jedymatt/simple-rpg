import json

from models import Attribute
from models import Modifier


def load_modifiers():
    with open('modifiers.json') as _json_file:
        modifiers = []
        for modifier in json.load(_json_file):
            modifiers.append(
                Modifier(
                    prefix=modifier['prefix'],
                    attribute=Attribute(
                        **modifier['attribute']
                    ),
                    bonus_exp=modifier['bonus_exp'],
                    bonus_money=modifier['bonus_money']
                )
            )
    return modifiers
# session.add_all(modifiers)
# session.commit()
