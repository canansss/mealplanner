from fastapi import FastAPI

app = FastAPI(title="Akıllı Aile Yemek Planlayıcı", version="1.0")

@app.get("/")
def read_root():
    return {"message": "Akıllı Aile Yemek Planlayıcı API çalışıyor!"}