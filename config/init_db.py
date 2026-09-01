from config.db import Base, engine
import authentication.models  
import meals.models  
import orders.models  

Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")
