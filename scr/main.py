"""
Главный файл приложения
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from scr.core.config import settings
from scr.api import main_router
from scr.api.auth import router as auth_router
from scr.api.users import router as users_router
from scr.api.contracts import router as contracts_router
from scr.api.bookings import router as bookings_router
from scr.api.trainer_schedule import router as trainer_router
from scr.api.gym import router as gym_router
from scr.api.lockers import router as lockers_router
from scr.api.clients import router as clients_router
from scr.api.attendance import router as attendance_router
from scr.api.services import router as services_router
from scr.api.zones import router as zones_router
from scr.api.schedule import router as schedule_router
from scr.api.passes import router as passes_router
from scr.db.database import engine
from scr.payment.api import router as payment_router
from sqlalchemy import text

# Создание приложения
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов и шаблонов
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass  # Если папки static нет, просто пропускаем

# Подключение роутеров
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(contracts_router)
app.include_router(bookings_router)
app.include_router(trainer_router)
app.include_router(gym_router)
app.include_router(lockers_router)
app.include_router(clients_router)
app.include_router(attendance_router)
app.include_router(services_router)
app.include_router(zones_router)
app.include_router(schedule_router)
app.include_router(passes_router)
app.include_router(main_router)
app.include_router(payment_router)

@app.on_event("startup")
def _startup_migrations() -> None:
    """
    Минимальная авто-миграция схемы без Alembic.
    Нужна, чтобы уже созданная БД не ломалась после добавления новых колонок.
    """
    try:
        if engine.dialect.name == "postgresql":
            with engine.begin() as conn:
                # Зал для расписания тренера
                conn.execute(text("ALTER TABLE trainer_schedules ADD COLUMN IF NOT EXISTS gym_zone_id INTEGER"))

                # Колонки для логики "занятие проведено" в расписании
                conn.execute(text("ALTER TABLE training_sessions ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT FALSE"))
                conn.execute(text("ALTER TABLE training_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP"))

                # История посещений для тренера (для проведенных тренировок)
                conn.execute(text("ALTER TABLE visits ADD COLUMN IF NOT EXISTS trainer_id UUID"))

                # Чтобы не было дублей посещений по одному занятию
                conn.execute(text("ALTER TABLE visits ADD COLUMN IF NOT EXISTS training_session_id UUID"))
    except Exception as e:
        # Не падаем при старте, но печатаем предупреждение
        print(f"[startup migrations] warning: {e}")

    # Создаем новые таблицы/индексы если их еще нет
    try:
        from scr.db import models
        from scr.db.models import Base
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[startup create_all] warning: {e}")

    # Сидинг базовых залов, если таблица пустая
    try:
        from scr.db.database import SessionLocal
        from scr.db.models import GymZone

        db = SessionLocal()
        try:
            zones_count = db.query(GymZone).count()
            if zones_count == 0:
                db.add_all([
                    GymZone(name="Тренажерный зал", description="Основной зал с тренажерами", capacity=50, is_active=True),
                    GymZone(name="Зал групповых занятий", description="Зона для групповых тренировок", capacity=30, is_active=True),
                    GymZone(name="Бассейн", description="Зона бассейна", capacity=20, is_active=True),
                ])
                db.commit()
                print("[startup seed] default gym zones created")
        finally:
            db.close()
    except Exception as e:
        print(f"[startup seed] warning: {e}")


@app.get("/")
async def root():
    """Корневой endpoint"""
    try:
        return FileResponse("templates/index.html")
    except:
        return {
            "message": "Gym Management System API",
            "version": settings.APP_VERSION,
            "docs": "/api/docs"
        }


@app.get("/login")
async def login_page():
    """Страница входа"""
    try:
        return FileResponse("templates/login.html")
    except:
        return {"message": "Login page"}


@app.get("/dashboard")
async def dashboard_page():
    """Страница дашборда"""
    try:
        return FileResponse("templates/dashboard.html")
    except:
        return {"message": "Dashboard page"}


@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "scr.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD
    )

