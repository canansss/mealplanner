from sqlalchemy import Column, Integer, String, Date, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=True)
    category = Column(String, nullable=True)  # Örn: Çorba, Ana Yemek, Tatlı
    ingredients = Column(Text, nullable=True)  # Malzemeler listesi
    video_url = Column(String, nullable=True)  # YouTube linki
    available_months = Column(String, nullable=True)  # Virgüllü ay listesi (1-12), boşsa her ay uygun
    is_fish = Column(Boolean, default=False, nullable=False)
    tags = Column(String, nullable=True)  # Virgüllü etiketler

    preferences = relationship("UserMealPreference", back_populates="meal", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    pin_hash = Column(String, nullable=False)

    preferences = relationship("UserMealPreference", back_populates="user", cascade="all, delete-orphan")
    schedules = relationship("UserSchedule", back_populates="user", cascade="all, delete-orphan")


class UserMealPreference(Base):
    __tablename__ = "user_meal_preferences"
    __table_args__ = (UniqueConstraint("user_id", "meal_id", name="uq_user_meal"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=False)
    preference = Column(String, nullable=False)  # OK / NO / MAYBE / VETO

    user = relationship("User", back_populates="preferences")
    meal = relationship("Meal", back_populates="preferences")


class UserSchedule(Base):
    __tablename__ = "user_schedules"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    is_home = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="schedules")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    meal_type = Column(String, nullable=False)  # Örn: Öğle, Akşam
    meal_name = Column(String, nullable=False)
    meal_id = Column(Integer, ForeignKey("meals.id"), nullable=True)

    meal = relationship("Meal")


class StockItem(Base):
    __tablename__ = "stock_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity_text = Column(String, nullable=True)
    updated_at = Column(Date, nullable=True)
    source = Column(String, default="manual", nullable=False)  # manual / ai_detected
    photo_path = Column(String, nullable=True)
    needs_review = Column(Boolean, default=False, nullable=False)


class Rule(Base):
    __tablename__ = "rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    rule_type = Column(String, nullable=False)  # Örn: min_per_week
    target_tag = Column(String, nullable=True)  # Örn: fish
    min_count = Column(Integer, default=1, nullable=False)
    period = Column(String, default="week", nullable=False)
    active = Column(Boolean, default=True, nullable=False)
