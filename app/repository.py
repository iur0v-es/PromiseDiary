from datetime import datetime, timezone

from app.database import get_connection
from app.schemas import TaskCreate, TaskRead


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