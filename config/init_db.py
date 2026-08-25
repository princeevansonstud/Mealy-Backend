from config.db import Base, engine
from authentication.models import User

Base.metadata.create_all(bind=engine)

print("Users table created successfully.")