from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# 1. Aile Üyeleri Tablosu
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    schedule_type = Column(String, default="adult_home") # adult_home, school_kid, toddler
    portion_multiplier = Column(Float, default=1.0)
    is_picky_eater = Column(Boolean, default=False)
    safe_foods = Column(String) # Virgülle ayrılmış güvenli yemekler

# 2. Yemek Tarifleri Tablosu
class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String) # main_fish, fast_food, manav vb.
    main_protein_tag = Column(String) # balık, tavuk, kıyma vb.
    cooking_method = Column(String) # fırın, ocak vb.
    default_servings = Column(Integer, default=4)
    image_url = Column(String)

# 3. Kiler / Envanter Tablosu
class Pantry(Base):
    __tablename__ = "pantry"

    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String, nullable=False)
    stock_quantity = Column(Float, default=0.0)
    unit = Column(String) # gr, adet, şişe vb.

# 4. Haftalık Plan Tablosu
class WeeklyPlan(Base):
    __tablename__ = "weekly_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_date = Column(Date, nullable=False)
    meal_type = Column(String, default="dinner") # lunch, dinner
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    status = Column(String, default="draft") # draft, finalized, vetoed
    
    recipe = relationship("Recipe")