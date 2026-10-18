from fastapi import FastAPI

app = FastAPI(title="Дневник обещаний")


@app.get("/")
def root():
    return {"message": "Дневник обещаний работает"}