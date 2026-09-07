from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import hash_pin, verify_pin, set_session_cookie, clear_session_cookie, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.name == user.name).first():
        raise HTTPException(status_code=400, detail="Bu isimde bir kullanıcı zaten var")
    db_user = models.User(name=user.name, pin_hash=hash_pin(user.pin))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.get("/", response_model=List[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@router.post("/login/", response_model=schemas.UserResponse)
def login(credentials: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.name == credentials.name).first()
    if not user or not verify_pin(credentials.pin, user.pin_hash):
        raise HTTPException(status_code=401, detail="İsim veya PIN hatalı")
    set_session_cookie(response, user.id)
    return user


@router.post("/logout/")
def logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Çıkış yapıldı"}


@router.get("/me/", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}/preferences/", response_model=List[schemas.PreferenceResponse])
def get_preferences(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.UserMealPreference).filter(
        models.UserMealPreference.user_id == user_id
    ).all()


@router.put("/{user_id}/preferences/{meal_id}", response_model=schemas.PreferenceResponse)
def set_preference(
    user_id: int,
    meal_id: int,
    payload: schemas.PreferenceSet,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sadece kendi tercihlerinizi değiştirebilirsiniz")
    if not db.query(models.Meal).filter(models.Meal.id == meal_id).first():
        raise HTTPException(status_code=404, detail="Yemek bulunamadı")

    pref = db.query(models.UserMealPreference).filter(
        models.UserMealPreference.user_id == user_id,
        models.UserMealPreference.meal_id == meal_id,
    ).first()
    if pref:
        pref.preference = payload.preference.value
    else:
        pref = models.UserMealPreference(user_id=user_id, meal_id=meal_id, preference=payload.preference.value)
        db.add(pref)
    db.commit()
    db.refresh(pref)
    return pref


@router.get("/{user_id}/schedule/", response_model=List[schemas.ScheduleResponse])
def get_schedule(
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.UserSchedule).filter(models.UserSchedule.user_id == user_id)
    if start_date:
        query = query.filter(models.UserSchedule.date >= start_date)
    if end_date:
        query = query.filter(models.UserSchedule.date <= end_date)
    return query.order_by(models.UserSchedule.date).all()


@router.put("/{user_id}/schedule/{schedule_date}", response_model=schemas.ScheduleResponse)
def set_schedule(
    user_id: int,
    schedule_date: date,
    payload: schemas.ScheduleSet,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sadece kendi programınızı değiştirebilirsiniz")

    entry = db.query(models.UserSchedule).filter(
        models.UserSchedule.user_id == user_id,
        models.UserSchedule.date == schedule_date,
    ).first()
    if entry:
        entry.is_home = payload.is_home
    else:
        entry = models.UserSchedule(user_id=user_id, date=schedule_date, is_home=payload.is_home)
        db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
