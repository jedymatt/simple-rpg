import os

import yaml
from sqlalchemyseed import HybridSeeder

from db import session


seeder = HybridSeeder(session=session)


def seed(filepath: str):
    with open(filepath, 'r') as f:
        data = yaml.load(f.read(), Loader=yaml.SafeLoader)

    seeder.seed(data)


path_dir = 'data'
filetype = 'yaml'

filepaths = []
for fname in os.listdir(path_dir):
    if fname.endswith('.yaml'):
        filepaths.append(os.path.join(path_dir, fname))


filepaths.sort()

for filepath in filepaths:
    seed(filepath)

# session.commit()
