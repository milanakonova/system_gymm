"""
Сервис для работы со шкафчиками
"""
import random
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session

from scr.db.models import Locker, User
from scr.db.repositories.locker_repository import LockerRepository
from scr.db.repositories.user_repository import UserRepository


class LockerService:
    def __init__(self, db: Session):
        self.db = db
        self.locker_repo = LockerRepository(db)
        self.user_repo = UserRepository(db)

    def assign_locker_to_user(self, user_id: UUID, gender: str) -> Optional[Locker]:
        """
        Назначение шкафчика пользователю
        gender: "male" -> "men", "female" -> "women"
        """
        # Преобразуем пол для раздевалки
        locker_gender = "men" if gender == "male" else "women"

        # Ищем свободный шкафчик
        available_lockers = self.locker_repo.get_available(locker_gender)
        if not available_lockers:
            return None

        # Берем первый доступный
        locker = available_lockers[0]

        # Генерируем новый код
        new_code = random.randint(1000, 9999)

        # Обновляем шкафчик
        locker.status = "occupied"
        locker.code = new_code
        locker.occupied_by_user_id = user_id
        locker.occupied_at = datetime.now(timezone.utc)

        return self.locker_repo.update(locker)

    def release_locker(self, locker_id: int) -> Locker:
        """Освобождение шкафчика"""
        locker = self.locker_repo.get_by_id(locker_id)
        if not locker:
            raise ValueError(f"Шкафчик с ID {locker_id} не найден")

        # Генерируем новый код
        new_code = random.randint(1000, 9999)

        # Освобождаем шкафчик
        locker.status = "free"
        locker.code = new_code
        locker.occupied_by_user_id = None
        locker.occupied_at = None

        return self.locker_repo.update(locker)

    def get_user_locker(self, user_id: UUID) -> Optional[Locker]:
        """Получение шкафчика пользователя"""
        lockers = self.locker_repo.get_all()
        for locker in lockers:
            if locker.occupied_by_user_id == user_id and locker.status == "occupied":
                return locker
        return None

