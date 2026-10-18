from fastapi import FastAPI

from app.schemas import TaskCreate

app = FastAPI(title="Дневник обещаний")


@app.get("/")
def root():
    return {"message": "Дневник обещаний работает"}


@app.post("/tasks")
def create_task(task: TaskCreate):
    return task