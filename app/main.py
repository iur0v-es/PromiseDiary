from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

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

@app.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(task_id: int):
    try:
        task = repository.get_task(task_id)
    except ValidationError:
        raise HTTPException(
            status_code=409,
            detail="Запись дела повреждена. Исходные данные сохранены в базе.",
        ) from None

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Дело не найдено",
        )

    return task