from datetime import datetime, timezone
from pydantic import ValidationError

from app.database import get_connection
from app.schemas import TaskCreate, TaskRead, TaskList


def create_task(task: TaskCreate) -> TaskRead:
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks (
                title,
                description,
                promised_on,
                due_on,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                task.title,
                task.description,
                task.promised_on.isoformat(),
                task.due_on.isoformat(),
                now,
                now,
            ),
        )

        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return TaskRead.model_validate(dict(row))

def get_tasks() -> TaskList:
    tasks = []
    warnings = []

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM tasks
            ORDER BY due_on, id
            """
        ).fetchall()

    for row in rows:
        try:
            task = TaskRead.model_validate(dict(row))
        except ValidationError:
            warnings.append(
                f"Дело №{row['id']} повреждено и пропущено. "
                "Исходная запись сохранена в базе."
            )
        else:
            tasks.append(task)

    return TaskList(tasks=tasks, warnings=warnings)