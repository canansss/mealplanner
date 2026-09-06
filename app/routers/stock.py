import os
import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.services.vision import analyze_stock_image

router = APIRouter(prefix="/stock", tags=["Stock"])

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads", "stock")
IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.get("/", response_model=List[schemas.StockItemResponse])
def list_stock(db: Session = Depends(get_db)):
    return db.query(models.StockItem).all()


@router.post("/", response_model=schemas.StockItemResponse)
def add_stock_item(item: schemas.StockItemCreate, db: Session = Depends(get_db)):
    db_item = models.StockItem(
        name=item.name, quantity_text=item.quantity_text, source="manual", updated_at=date.today()
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.put("/{item_id}", response_model=schemas.StockItemResponse)
def update_stock_item(item_id: int, item: schemas.StockItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stok kalemi bulunamadı")
    for field, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    db_item.updated_at = date.today()
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{item_id}")
def delete_stock_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.StockItem).filter(models.StockItem.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Stok kalemi bulunamadı")
    db.delete(db_item)
    db.commit()
    return {"message": "Stok kalemi silindi"}


@router.post("/scan/")
async def scan_stock(file: UploadFile = File(...), db: Session = Depends(get_db)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1] or ".bin"
    stored_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{extension}")
    contents = await file.read()
    with open(stored_path, "wb") as f:
        f.write(contents)

    if file.content_type not in IMAGE_CONTENT_TYPES:
        return {
            "status": "stored_only",
            "message": "Video/desteklenmeyen görsel formatı kaydedildi. Ürünleri /stock/ ile manuel ekleyin.",
            "photo_path": stored_path,
        }

    detected = analyze_stock_image(contents, media_type=file.content_type)
    if detected is None:
        return {
            "status": "pending_manual_review",
            "message": "ANTHROPIC_API_KEY tanımlı değil. Fotoğraf kaydedildi, ürünleri /stock/ ile manuel ekleyin.",
            "photo_path": stored_path,
        }

    created_items = []
    for entry in detected:
        db_item = models.StockItem(
            name=entry.get("name", "bilinmeyen ürün"),
            quantity_text=entry.get("quantity_text"),
            source="ai_detected",
            photo_path=stored_path,
            needs_review=True,
            updated_at=date.today(),
        )
        db.add(db_item)
        created_items.append(db_item)
    db.commit()
    for item in created_items:
        db.refresh(item)

    return {
        "status": "ai_detected",
        "message": f"{len(created_items)} ürün tespit edildi, lütfen onaylayın.",
        "items": [schemas.StockItemResponse.model_validate(i) for i in created_items],
    }
