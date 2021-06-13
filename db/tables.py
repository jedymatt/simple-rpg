from db.connector import engine
from models import Base


def create():
    Base.metadata.create_all(engine)


def drop():
    Base.metadata.drop_all(engine)
