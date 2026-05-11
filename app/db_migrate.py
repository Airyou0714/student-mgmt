"""SQLite 轻量迁移：兼容旧库（含 class_name 的 students 表）。"""

from sqlalchemy import inspect, text

from app.extensions import db


def run_sqlite_migrations() -> None:
    if db.engine.dialect.name != "sqlite":
        return

    insp = inspect(db.engine)
    if not insp.has_table("students"):
        return

    cols = {c["name"] for c in insp.get_columns("students")}

    if "class_id" not in cols:
        with db.engine.begin() as conn:
            conn.execute(
                text("ALTER TABLE students ADD COLUMN class_id INTEGER")
            )

    if "class_name" in cols:
        with db.engine.begin() as conn:
            try:
                conn.execute(text("ALTER TABLE students DROP COLUMN class_name"))
            except Exception:
                pass
