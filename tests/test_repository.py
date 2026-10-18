import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app import database, repository
from app.schemas import TaskCreate, CommentCreate


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary_directory = TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)

        directory = Path(temporary_directory.name)

        patcher = patch.multiple(
            database,
            DATA_DIR=directory,
            DATABASE_PATH=directory / "test.sqlite3",
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        database.init_db()

    def create_task(self, title):
        return repository.create_task(
            TaskCreate(
                title=title,
                description="Тестовое дело",
                promised_on="2026-10-18",
                due_on="2026-10-25",
            )
        )

    def test_corrupted_task_does_not_hide_other_tasks(self):
        good = self.create_task("Исправное дело")
        damaged = self.create_task("Повреждённое дело")

        with database.get_connection() as connection:
            connection.execute(
                "UPDATE tasks SET created_at = ? WHERE id = ?",
                ("invalid timestamp", damaged.id),
            )

        result = repository.get_tasks()

        self.assertEqual(
            [task.id for task in result.tasks],
            [good.id],
        )
        self.assertEqual(len(result.warnings), 1)

        # Повреждённая запись не удалена.
        with database.get_connection() as connection:
            row = connection.execute(
                "SELECT created_at FROM tasks WHERE id = ?",
                (damaged.id,),
            ).fetchone()

        self.assertEqual(row["created_at"], "invalid timestamp")

    def test_corrupted_comment_does_not_hide_other_comments(self):
        task = self.create_task("Дело с комментариями")

        good = repository.create_comment(
            task.id,
            CommentCreate(text="Исправный комментарий"),
        )
        damaged = repository.create_comment(
            task.id,
            CommentCreate(text="Повреждённый комментарий"),
        )

        with database.get_connection() as connection:
            connection.execute(
                "UPDATE comments SET created_at = ? WHERE id = ?",
                ("invalid timestamp", damaged.id),
            )

        result = repository.get_comments(task.id)

        self.assertEqual(
            [comment.id for comment in result.comments],
            [good.id],
        )
        self.assertEqual(len(result.warnings), 1)

        with database.get_connection() as connection:
            row = connection.execute(
                "SELECT created_at FROM comments WHERE id = ?",
                (damaged.id,),
            ).fetchone()

        self.assertEqual(row["created_at"], "invalid timestamp")

    def test_repeated_initialization_preserves_data(self):
        task = self.create_task("Сохранённое дело")

        repository.create_comment(
            task.id,
            CommentCreate(text="Сохранённый комментарий"),
        )

        database.init_db()

        restored_task = repository.get_task(task.id)
        restored_comments = repository.get_comments(task.id)

        self.assertEqual(restored_task.title, "Сохранённое дело")
        self.assertEqual(len(restored_comments.comments), 1)
        self.assertEqual(
            restored_comments.comments[0].text,
            "Сохранённый комментарий",
        )


if __name__ == "__main__":
    unittest.main()