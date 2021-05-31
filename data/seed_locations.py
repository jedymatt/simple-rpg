import json

from models import Location
from db import session

with open('locations.json') as _json_file:
    locations = []
    for _location in json.load(_json_file):
        locations.append(
            Location(
                **_location
            )
        )

session.add_all(locations)

session.commit()
