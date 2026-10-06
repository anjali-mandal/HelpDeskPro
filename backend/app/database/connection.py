from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./helpdeskpro.db")


engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)


def ensure_schema():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if "notifications" in table_names:
        notification_columns = {
            column["name"] for column in inspector.get_columns("notifications")
        }
        if "title" not in notification_columns:
            with engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE notifications "
                    "ADD COLUMN title VARCHAR(200) DEFAULT 'Notification'"
                ))

    if "tickets" in table_names:
        ticket_columns = {column["name"] for column in inspector.get_columns("tickets")}
        if "sla_breached" not in ticket_columns:
            with engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE tickets ADD COLUMN sla_breached BOOLEAN DEFAULT FALSE"
                ))

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()