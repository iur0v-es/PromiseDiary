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