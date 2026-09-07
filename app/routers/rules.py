from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.planner import check_rules

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.get("/", response_model=List[schemas.RuleResponse])
def list_rules(db: Session = Depends(get_db)):
    return db.query(models.Rule).all()


@router.post("/", response_model=schemas.RuleResponse)
def create_rule(rule: schemas.RuleCreate, db: Session = Depends(get_db)):
    db_rule = models.Rule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.put("/{rule_id}", response_model=schemas.RuleResponse)
def update_rule(rule_id: int, rule: schemas.RuleCreate, db: Session = Depends(get_db)):
    db_rule = db.query(models.Rule).filter(models.Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    for field, value in rule.model_dump().items():
        setattr(db_rule, field, value)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = db.query(models.Rule).filter(models.Rule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Kural bulunamadı")
    db.delete(db_rule)
    db.commit()
    return {"message": "Kural silindi"}


@router.get("/check/", response_model=List[schemas.RuleViolation])
def check_rules_endpoint(start_date: date, end_date: date, db: Session = Depends(get_db)):
    return check_rules(db, start_date, end_date)
