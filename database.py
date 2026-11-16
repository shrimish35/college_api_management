from collections.abc import Generator
from pathlib import Path
from sqlite3 import Connection

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry


DATABASE_URL = f"sqlite:///{Path(__file__).resolve().with_name('college.db')}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


@event.listens_for(engine, "connect")
def enable_foreign_keys(connection: Connection, connection_record: ConnectionPoolEntry) -> None:
    connection.execute("PRAGMA foreign_keys=ON")


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session