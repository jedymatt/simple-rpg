import yaml
from sqlalchemyseed import Seeder

from db.connector import session


def load_entities_from_yaml(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f.read())


entities = load_entities_from_yaml('locations.yaml')

seeder = Seeder()
seeder.seed(entities, session)

print(seeder.instances)

print(entities)
# yaml.dump(entities, open('locations.yaml', 'r+'), sort_keys=False)


# session.commit()
