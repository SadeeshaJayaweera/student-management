"""
NSBM EduSphere — Database Migration Lifecycle & Rollback Tests
Verifies Alembic upgrade to head, schema verification, and clean downgrade rollback
"""
import os
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_and_downgrade(tmp_path):
    """Verify full migration lifecycle: upgrade to head, inspect schema, downgrade to base, re-upgrade"""
    test_db_file = tmp_path / "test_migration.db"
    sync_db_url = f"sqlite:///{test_db_file}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", sync_db_url)

    # 1. Upgrade to head
    command.upgrade(alembic_cfg, "head")

    # 2. Inspect created tables
    engine = create_engine(sync_db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    required_tables = {
        "users", "students", "lecturers", "alumni", "courses",
        "enrollments", "grades", "attendance", "assignments",
        "assignment_submissions", "books", "borrow_records", "clubs",
        "club_events", "news", "notifications", "messages"
    }
    for table in required_tables:
        assert table in tables, f"Expected table '{table}' was not created by Alembic migration"

    # Verify column constraints on users table
    columns = {col["name"]: col for col in inspector.get_columns("users")}
    assert "email" in columns
    assert "hashed_password" in columns
    assert "role" in columns

    # 3. Downgrade to base (clean rollback verification)
    command.downgrade(alembic_cfg, "base")
    inspector_post_downgrade = inspect(engine)
    remaining_tables = [t for t in inspector_post_downgrade.get_table_names() if t != "alembic_version"]
    assert len(remaining_tables) == 0, f"Found orphaned tables after downgrade: {remaining_tables}"

    # 4. Re-upgrade to head (reproducibility check)
    command.upgrade(alembic_cfg, "head")
    inspector_re_upgrade = inspect(engine)
    for table in required_tables:
        assert table in inspector_re_upgrade.get_table_names()

    engine.dispose()
