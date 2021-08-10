import os

from sqlalchemyseed import HybridSeeder, load_entities_from_yaml, validator

from db import session


seeder = HybridSeeder(session=session)

path_dir = 'data'
filetypes = ['yaml', 'yml']

filepaths = [os.path.join(path_dir, fname) for fname in os.listdir(
    path_dir) if not fname.startswith('_') and fname.rsplit('.')[1] in filetypes]

filepaths.sort()
# print(filepaths)
for filepath in filepaths:
    print('-' * 75)
    print(f'{filepath}:', end='')
    entities = load_entities_from_yaml(filepath)
    validator.SchemaValidator.validate(entities)

    print('PASSED')
    # print(filepath, ':', seeder.instances)

# session.commit()
