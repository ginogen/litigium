from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "message": "API funcionando correctamente"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Litigium API"}

handler = Mangum(app, lifespan="off") 