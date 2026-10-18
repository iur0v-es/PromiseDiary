from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from datetime import date
from typing import Literal

from app import repository
from app.database import init_db
from app.schemas import (
    TaskCreate,
    TaskRead,
    TaskList,
    TaskUpdate,
    TaskStatusUpdate,
    CommentCreate,
    CommentRead,
    CommentList
)


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
def get_tasks(
    q: str = "",
    status: Literal["open", "closed"] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=422,
            detail="Начало периода не может быть позже конца",
        )

    return repository.get_tasks(
        q=q,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

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

@app.put("/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task: TaskUpdate):
    try:
        updated_task = repository.update_task(task_id, task)
    except ValidationError:
        raise HTTPException(
            status_code=409,
            detail="Запись дела повреждена. Изменения отменены.",
        ) from None

    if updated_task is None:
        raise HTTPException(
            status_code=404,
            detail="Дело не найдено",
        )

    return updated_task

@app.patch("/tasks/{task_id}/status", response_model=TaskRead)
def update_task_status(task_id: int, data: TaskStatusUpdate):
    try:
        task = repository.update_task_status(task_id, data.status)
    except ValidationError:
        raise HTTPException(
            status_code=409,
            detail="Запись дела повреждена. Изменение статуса отменено.",
        ) from None

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Дело не найдено",
        )

    return task

@app.post(
    "/tasks/{task_id}/comments",
    response_model=CommentRead,
    status_code=201,
)
def create_comment(task_id: int, comment: CommentCreate):
    try:
        created_comment = repository.create_comment(task_id, comment)
    except ValidationError:
        raise HTTPException(
            status_code=409,
            detail="Данные дела или комментария повреждены. "
                   "Добавление отменено.",
        ) from None

    if created_comment is None:
        raise HTTPException(
            status_code=404,
            detail="Дело не найдено",
        )

    return created_comment

@app.get(
    "/tasks/{task_id}/comments",
    response_model=CommentList,
)
def get_comments(task_id: int):
    try:
        result = repository.get_comments(task_id)
    except ValidationError:
        raise HTTPException(
            status_code=409,
            detail="Запись дела повреждена. "
                   "Исходные данные сохранены в базе.",
        ) from None

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Дело не найдено",
        )

    return result