from db import engine
from models.models import Base


def create():
    Base.metadata.create_all(engine)


def drop():
    Base.metadata.drop_all(engine)
