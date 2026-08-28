from config.db import Base, engine
from authentication.models import User
from meals.models import MealOption, DailyMenu, DailyMenuItem

Base.metadata.create_all(engine)
print("Tables created successfully.")