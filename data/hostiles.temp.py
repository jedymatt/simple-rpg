from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemyseeder import ResolvingSeeder

import models
from models import Base

engine = create_engine("sqlite://", future=True)

Session = sessionmaker(bind=engine)
session = Session()
seeder = ResolvingSeeder(session)

Base.metadata.create_all(engine)

new_entities = seeder.load_entities_from_json_file("hostiles.temp.json")

print(new_entities)
# session.add_all(new_entities)


for hostile in session.query(models.Hostile).all():
    print(hostile, hostile.attribute)
