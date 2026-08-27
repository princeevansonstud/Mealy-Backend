from config.db import Base, engine
import authentication.models  # Register SQLAlchemy mappings before creating tables.
import meals.models  # Register SQLAlchemy mappings before creating tables.
import orders.models  # Register SQLAlchemy mappings before creating tables.

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")
