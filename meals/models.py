from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from config.db import Base


class MealOption(Base):
    __tablename__ = "meal_options"

    id = Column(Integer, primary_key=True, index=True)
    caterer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)


class DailyMenu(Base):
    __tablename__ = "daily_menus"

    id = Column(Integer, primary_key=True, index=True)
    caterer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    menu_date = Column(Date, nullable=False)


class DailyMenuItem(Base):
    __tablename__ = "daily_menu_items"

    id = Column(Integer, primary_key=True, index=True)
    daily_menu_id = Column(Integer, ForeignKey("daily_menus.id"), nullable=False)
    meal_option_id = Column(Integer, ForeignKey("meal_options.id"), nullable=False)

