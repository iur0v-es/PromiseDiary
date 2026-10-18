from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.schemas import TaskCreate


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Дневник обещаний",
    lifespan=lifespan,
)


@app.get("/")
def root():
    return {"message": "Дневник обещаний работает"}


@app.post("/tasks")
def create_task(task: TaskCreate):
    return task