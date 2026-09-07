from dotenv import load_dotenv

load_dotenv()

import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import date
from sqlalchemy import text

from app.database import engine, Base, get_db
from app import models
from app.routers import meals, meal_plans, users, rules, stock

# Veritabanı tablolarını otomatik oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Akıllı Aile Yemek Planlayıcı", version="2.0")

# Router'ları ana uygulamaya dahil et
app.include_router(meals.router)
app.include_router(meal_plans.router)
app.include_router(users.router)
app.include_router(rules.router)
app.include_router(stock.router)

_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/ui", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

@app.get("/")
def read_root():
    return {"message": "Akıllı Aile Yemek Planlayıcı API modüler yapısıyla çalışıyor!"}

# --- SİSTEM VE YARDIMCI ENDPOINTLER ---

@app.get("/health/")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status
    }

@app.get("/stats/")
def get_system_stats(db: Session = Depends(get_db)):
    total_meals = db.query(models.Meal).count()
    total_plans = db.query(models.MealPlan).count()
    return {
        "total_registered_meals": total_meals,
        "total_meal_plans": total_plans
    }

@app.get("/info/")
def get_system_info():
    return {
        "app_name": "Akıllı Aile Yemek Planlayıcı",
        "version": "2.0",
        "description": "FastAPI, SQLAlchemy ve Router mimarisiyle yapılandırılmış aile yemek sistemi."
    }

@app.get("/logs/summary/")
def get_logs_summary():
    return {
        "status": "active",
        "logging_level": "INFO",
        "recent_events": [
            "Modular router architecture refactoring completed successfully",
            "All endpoints mapped and active"
        ]
    }

@app.get("/export/json/")
def export_database(db: Session = Depends(get_db)):
    db_meals = db.query(models.Meal).all()
    plans = db.query(models.MealPlan).all()
    
    return {
        "meals": [{"id": m.id, "name": m.name, "category": m.category, "ingredients": m.ingredients} for m in db_meals],
        "meal_plans": [{"id": p.id, "date": str(p.date), "meal_type": p.meal_type, "meal_name": p.meal_name} for p in plans]
    }

@app.get("/shopping-list/")
def generate_shopping_list(start_date: date, end_date: date, db: Session = Depends(get_db)):
    plans = db.query(models.MealPlan).filter(
        models.MealPlan.date >= start_date,
        models.MealPlan.date <= end_date
    ).all()
    
    meal_names = [plan.meal_name for plan in plans]
    db_meals = db.query(models.Meal).filter(models.Meal.name.in_(meal_names)).all()
    ingredients_list = [meal.ingredients for meal in db_meals if meal.ingredients]
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "planned_meals": meal_names,
        "shopping_list": ingredients_list
    }

@app.delete("/reset-database/")
def reset_database(db: Session = Depends(get_db)):
    try:
        db.query(models.MealPlan).delete()
        db.query(models.Meal).delete()
        db.commit()
        return {"message": "Tüm veritabanı başarıyla sıfırlandı."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sıfırlama hatası: {str(e)}")