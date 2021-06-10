import json

from models import Raw


def load_items():
    with open('items.json') as _json_file:
        items = []
        for item in json.load(_json_file):
            if item['type'] == 'raw':
                items.append(
                    Raw(
                        **item
                    )
                )

    return items

# session.add_all(items)
# session.commit()
