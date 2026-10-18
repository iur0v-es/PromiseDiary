from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10000)
    promised_on: date
    due_on: date

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Название не может быть пустым")

        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskCreate":
        if self.due_on < self.promised_on:
            raise ValueError(
                "Срок завершения не может быть раньше даты обещания"
            )

        return self

class TaskRead(TaskCreate):
    id: int
    status: Literal["open", "closed"]
    created_at: datetime
    updated_at: datetime

class TaskList(BaseModel):
    tasks: list[TaskRead]
    warnings: list[str] = Field(default_factory=list)

class TaskUpdate(TaskCreate):
    pass

class TaskStatusUpdate(BaseModel):
    status: Literal["open", "closed"]

class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Комментарий не может быть пустым")

        return value


class CommentRead(CommentCreate):
    id: int
    task_id: int
    created_at: datetime


class CommentList(BaseModel):
    comments: list[CommentRead]
    warnings: list[str] = Field(default_factory=list)