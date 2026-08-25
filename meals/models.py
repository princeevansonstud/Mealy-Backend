from sqlalchemy import Column, Integer, String, Float
from config.db import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)
