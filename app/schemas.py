from pydantic import BaseModel, model_validator
from datetime import date
from typing import Optional, List
from enum import Enum


# --- Yemek (Meal) Şemaları ---
class MealBase(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    ingredients: Optional[str] = None
    video_url: Optional[str] = None
    available_months: Optional[str] = None  # "1,2,3" gibi, boşsa her ay uygun
    is_fish: bool = False
    tags: Optional[str] = None

    @model_validator(mode="after")
    def name_or_video_required(self):
        if not self.name and not self.video_url:
            raise ValueError("name veya video_url alanlarından en az biri gereklidir")
        return self


class MealCreate(MealBase):
    pass


class MealUpdate(MealBase):
    name: Optional[str] = None


class MealResponse(MealBase):
    id: int

    class Config:
        from_attributes = True


# --- Yemek Planı (MealPlan) Şemaları ---
class MealPlanBase(BaseModel):
    date: date
    meal_type: str  # Örn: Öğle, Akşam
    meal_name: str
    meal_id: Optional[int] = None


class MealPlanCreate(MealPlanBase):
    pass


class MealPlanResponse(MealPlanBase):
    id: int

    class Config:
        from_attributes = True


class MealPlanGenerateRequest(BaseModel):
    start_date: date
    end_date: date


# --- Kullanıcı (User) Şemaları ---
class UserCreate(BaseModel):
    name: str
    pin: str


class UserLogin(BaseModel):
    name: str
    pin: str


class UserResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class PreferenceValue(str, Enum):
    OK = "OK"
    NO = "NO"
    MAYBE = "MAYBE"
    VETO = "VETO"


class PreferenceSet(BaseModel):
    preference: PreferenceValue


class PreferenceResponse(BaseModel):
    meal_id: int
    preference: PreferenceValue

    class Config:
        from_attributes = True


class ScheduleSet(BaseModel):
    is_home: bool


class ScheduleResponse(BaseModel):
    date: date
    is_home: bool

    class Config:
        from_attributes = True


# --- Stok (StockItem) Şemaları ---
class StockItemBase(BaseModel):
    name: str
    quantity_text: Optional[str] = None


class StockItemCreate(StockItemBase):
    pass


class StockItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity_text: Optional[str] = None
    needs_review: Optional[bool] = None


class StockItemResponse(StockItemBase):
    id: int
    updated_at: Optional[date] = None
    source: str
    photo_path: Optional[str] = None
    needs_review: bool

    class Config:
        from_attributes = True


# --- Kural (Rule) Şemaları ---
class RuleBase(BaseModel):
    name: str
    rule_type: str = "min_per_week"
    target_tag: Optional[str] = None
    min_count: int = 1
    period: str = "week"
    active: bool = True


class RuleCreate(RuleBase):
    pass


class RuleResponse(RuleBase):
    id: int

    class Config:
        from_attributes = True


class RuleViolation(BaseModel):
    rule: RuleResponse
    period_start: date
    period_end: date
    actual_count: int
    satisfied: bool
