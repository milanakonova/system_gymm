"""
Подключение к базе данных
"""
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from scr.core.config import settings

# Создание движка с настройками для видимости изменений в pgAdmin
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    # Убеждаемся, что изменения видны сразу в pgAdmin
    isolation_level="READ COMMITTED",
    echo=False
)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Генератор сессий БД"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

