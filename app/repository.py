from datetime import datetime, timezone
from pydantic import ValidationError

from app.database import get_connection
from app.schemas import TaskCreate, TaskRead, TaskList, TaskUpdate
from app.schemas import CommentCreate, CommentRead

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

def get_task(task_id: int) -> TaskRead | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

    if row is None:
        return None

    return TaskRead.model_validate(dict(row))

def update_task(
    task_id: int,
    task: TaskUpdate,
) -> TaskRead | None:
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET title = ?,
                description = ?,
                promised_on = ?,
                due_on = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                task.title,
                task.description,
                task.promised_on.isoformat(),
                task.due_on.isoformat(),
                now,
                task_id,
            ),
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        return TaskRead.model_validate(dict(row))

def update_task_status(
    task_id: int,
    status: str,
) -> TaskRead | None:
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET status = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (status, now, task_id),
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        return TaskRead.model_validate(dict(row))

def create_comment(
    task_id: int,
    comment: CommentCreate,
) -> CommentRead | None:
    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:
        task_row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if task_row is None:
            return None

        TaskRead.model_validate(dict(task_row))

        cursor = connection.execute(
            """
            INSERT INTO comments (task_id, text, created_at)
            VALUES (?, ?, ?)
            """,
            (task_id, comment.text, now),
        )

        connection.execute(
            "UPDATE tasks SET updated_at = ? WHERE id = ?",
            (now, task_id),
        )

        row = connection.execute(
            "SELECT * FROM comments WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

        return CommentRead.model_validate(dict(row))