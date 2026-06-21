"""
Репозиторий для работы со шкафчиками
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from scr.db.models import Locker


class LockerRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, locker: Locker) -> Locker:
        """Создание шкафчика"""
        self.db.add(locker)
        self.db.commit()
        self.db.refresh(locker)
        return locker

    def get_by_id(self, locker_id: int) -> Optional[Locker]:
        """Получение шкафчика по ID"""
        return self.db.query(Locker).filter(Locker.id == locker_id).first()

    def get_all(self, gender: Optional[str] = None, status: Optional[str] = None) -> List[Locker]:
        """Получение всех шкафчиков с фильтрацией"""
        query = self.db.query(Locker)
        if gender:
            query = query.filter(Locker.gender == gender)
        if status:
            query = query.filter(Locker.status == status)
        return query.all()

    def get_available(self, gender: str) -> List[Locker]:
        """Получение доступных шкафчиков для указанного пола"""
        return self.db.query(Locker).filter(
            Locker.gender == gender,
            Locker.status == "free",
            Locker.is_available == True
        ).all()

    def update(self, locker: Locker) -> Locker:
        """Обновление шкафчика"""
        self.db.commit()
        self.db.refresh(locker)
        return locker

    def delete(self, locker: Locker) -> None:
        """Удаление шкафчика"""
        self.db.delete(locker)
        self.db.commit()

