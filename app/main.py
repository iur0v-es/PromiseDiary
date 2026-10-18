from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import repository
from app.database import init_db
from app.schemas import TaskCreate, TaskRead, TaskList


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


@app.post("/tasks", response_model=TaskRead, status_code=201)
def create_task(task: TaskCreate):
    return repository.create_task(task)

@app.get("/tasks", response_model=TaskList)
def get_tasks():
    return repository.get_tasks()