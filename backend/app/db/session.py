from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings


def configure_sqlite(engine: Engine) -> None:
    """WAL + FK enforcement + serialized writers for a SQLite engine.

    pysqlite/aiosqlite issue their own deferred BEGIN, which in WAL mode fails a
    read-then-write transaction with SQLITE_BUSY_SNAPSHOT (busy_timeout is not
    honored). So we disable the driver's transaction handling and emit
    BEGIN IMMEDIATE ourselves (SQLAlchemy "serializable isolation / savepoints"
    recipe).
    ponytail: global write lock per transaction — split read/write sessions if
    read latency under ingest load matters.
    """

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, _record) -> None:
        dbapi_connection.isolation_level = None
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")  # without it ondelete CASCADE/SET NULL is ignored
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn) -> None:
        conn.exec_driver_sql("BEGIN IMMEDIATE")


engine = create_async_engine(settings.database_url)
if engine.dialect.name == "sqlite":
    configure_sqlite(engine.sync_engine)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
