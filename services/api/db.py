import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# wczytujemy zmienne z .env
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://karma_user:karma_pass@localhost:5432/karma_db",
)

# engine SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,  # można zmienić na True przy debugowaniu
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def check_db_connection() -> bool:
    """
    Prosty health-check: sprawdza, czy da się wykonać SELECT 1.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # w logach uvicorna zobaczysz szczegóły, jeśli coś pójdzie nie tak
        print(f"DB connection failed: {exc}")
        return False
