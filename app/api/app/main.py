from fastapi import FastAPI
from app.database import engine, Base
from app.models import Base as ModelsBase

# Tabloları SQLite içinde otomatik oluştur
ModelsBase.metadata.create_all(bind=engine)

app = FastAPI(title="Akıllı Aile Yemek Planlayıcı", version="1.0")

@app.get("/")
def read_root():
    return {"message": "Akıllı Aile Yemek Planlayıcı API çalışıyor!"}