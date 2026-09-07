import random
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/meals", tags=["Meals"])


@router.post("/", response_model=schemas.MealResponse)
def create_meal(meal: schemas.MealCreate, db: Session = Depends(get_db)):
    db_meal = models.Meal(**meal.model_dump())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal


@router.get("/", response_model=List[schemas.MealResponse])
def list_meals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Meal).offset(skip).limit(limit).all()


@router.get("/category/{category}", response_model=List[schemas.MealResponse])
def meals_by_category(category: str, db: Session = Depends(get_db)):
    return db.query(models.Meal).filter(models.Meal.category == category).all()


@router.get("/search/", response_model=List[schemas.MealResponse])
def search_meals(keyword: str, db: Session = Depends(get_db)):
    pattern = f"%{keyword}%"
    return db.query(models.Meal).filter(
        or_(models.Meal.name.ilike(pattern), models.Meal.ingredients.ilike(pattern))
    ).all()


@router.get("/random-suggestion/", response_model=schemas.MealResponse)
def random_suggestion(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Meal)
    if category:
        query = query.filter(models.Meal.category == category)
    candidates = query.all()
    if not candidates:
        raise HTTPException(status_code=404, detail="Uygun yemek bulunamadı")
    return random.choice(candidates)


@router.get("/available/{month}", response_model=List[schemas.MealResponse])
def meals_available_in_month(month: int, db: Session = Depends(get_db)):
    if month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="Ay 1-12 arasında olmalıdır")
    all_meals = db.query(models.Meal).all()
    month_str = str(month)
    return [
        m for m in all_meals
        if not m.available_months or month_str in [p.strip() for p in m.available_months.split(",")]
    ]


@router.put("/{meal_id}", response_model=schemas.MealResponse)
def update_meal(meal_id: int, meal: schemas.MealUpdate, db: Session = Depends(get_db)):
    db_meal = db.query(models.Meal).filter(models.Meal.id == meal_id).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail="Yemek bulunamadı")
    for field, value in meal.model_dump(exclude_unset=True).items():
        setattr(db_meal, field, value)
    db.commit()
    db.refresh(db_meal)
    return db_meal


@router.delete("/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    db_meal = db.query(models.Meal).filter(models.Meal.id == meal_id).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail="Yemek bulunamadı")
    db.delete(db_meal)
    db.commit()
    return {"message": "Yemek silindi"}
