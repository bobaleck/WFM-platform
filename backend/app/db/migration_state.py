from sqlalchemy import text
from sqlalchemy.engine import Engine

BASELINE_REVISION = "20260526_0001"


def ensure_alembic_stamp(engine: Engine, revision: str = BASELINE_REVISION) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)"))
        current = connection.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar_one_or_none()
        if current is None:
            connection.execute(text("INSERT INTO alembic_version (version_num) VALUES (:revision)"), {"revision": revision})
