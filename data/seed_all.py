from db.connector import session
from seed_hostiles import load_hostiles
from seed_items import load_items
from seed_location_loots import load_location_loots
from seed_locations import load_locations
from seed_modifiers import load_modifiers

seeds = [load_locations, load_modifiers, load_items, load_hostiles, load_location_loots]

with session:
    for seed in seeds:
        session.add_all(seed())
        session.commit()
