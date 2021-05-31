from db import engine
from models.models import Base


Base.metadata.create_all(engine)
# Base.metadata.drop_all(engine)

