from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.planner import generate_plan

router = APIRouter(prefix="/meal-plans", tags=["Meal Plans"])


@router.post("/generate/", response_model=List[schemas.MealPlanResponse])
def generate_meal_plan(request: schemas.MealPlanGenerateRequest, db: Session = Depends(get_db)):
    if request.end_date < request.start_date:
        raise HTTPException(status_code=422, detail="end_date, start_date'ten önce olamaz")
    return generate_plan(db, request.start_date, request.end_date)


@router.post("/", response_model=schemas.MealPlanResponse)
def create_meal_plan(plan: schemas.MealPlanCreate, db: Session = Depends(get_db)):
    db_plan = models.MealPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.post("/bulk/", response_model=List[schemas.MealPlanResponse])
def create_meal_plans_bulk(plans: List[schemas.MealPlanCreate], db: Session = Depends(get_db)):
    db_plans = [models.MealPlan(**plan.model_dump()) for plan in plans]
    db.add_all(db_plans)
    db.commit()
    for db_plan in db_plans:
        db.refresh(db_plan)
    return db_plans


@router.get("/filter/", response_model=List[schemas.MealPlanResponse])
def filter_meal_plans(start_date: date, end_date: date, db: Session = Depends(get_db)):
    return db.query(models.MealPlan).filter(
        models.MealPlan.date >= start_date,
        models.MealPlan.date <= end_date
    ).order_by(models.MealPlan.date).all()


@router.get("/type/{meal_type}", response_model=List[schemas.MealPlanResponse])
def meal_plans_by_type(meal_type: str, db: Session = Depends(get_db)):
    return db.query(models.MealPlan).filter(models.MealPlan.meal_type == meal_type).all()


@router.put("/{plan_id}", response_model=schemas.MealPlanResponse)
def update_meal_plan(plan_id: int, plan: schemas.MealPlanCreate, db: Session = Depends(get_db)):
    db_plan = db.query(models.MealPlan).filter(models.MealPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    for field, value in plan.model_dump().items():
        setattr(db_plan, field, value)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.delete("/{plan_id}")
def delete_meal_plan(plan_id: int, db: Session = Depends(get_db)):
    db_plan = db.query(models.MealPlan).filter(models.MealPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı")
    db.delete(db_plan)
    db.commit()
    return {"message": "Plan silindi"}
