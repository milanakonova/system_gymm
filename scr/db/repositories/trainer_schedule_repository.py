"""
Репозиторий для работы с расписанием тренеров
"""
from typing import Optional, List
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from scr.db.models import TrainerSchedule


class TrainerScheduleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, schedule: TrainerSchedule) -> TrainerSchedule:
        """Создание записи расписания"""
        self.db.add(schedule)
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def get_by_id(self, schedule_id: int) -> Optional[TrainerSchedule]:
        """Получение расписания по ID"""
        return self.db.query(TrainerSchedule).filter(TrainerSchedule.id == schedule_id).first()

    def get_by_trainer_id(self, trainer_id: UUID) -> List[TrainerSchedule]:
        """Получение всего расписания тренера"""
        return self.db.query(TrainerSchedule).filter(
            TrainerSchedule.trainer_id == trainer_id
        ).all()

    def get_available_schedules(
        self,
        trainer_id: UUID,
        day_of_week: Optional[int] = None
    ) -> List[TrainerSchedule]:
        """Получение доступного расписания тренера"""
        query = self.db.query(TrainerSchedule).filter(
            TrainerSchedule.trainer_id == trainer_id,
            TrainerSchedule.is_working == True,
            TrainerSchedule.is_cancelled == False
        )
        if day_of_week is not None:
            query = query.filter(TrainerSchedule.day_of_week == day_of_week)
        return query.all()

    def get_all(
        self,
        trainer_id: Optional[UUID] = None,
        is_working: Optional[bool] = None
    ) -> List[TrainerSchedule]:
        """Получение всего расписания с фильтрацией"""
        query = self.db.query(TrainerSchedule)
        if trainer_id:
            query = query.filter(TrainerSchedule.trainer_id == trainer_id)
        if is_working is not None:
            query = query.filter(TrainerSchedule.is_working == is_working)
        return query.all()

    def update(self, schedule: TrainerSchedule) -> TrainerSchedule:
        """Обновление расписания"""
        self.db.commit()
        self.db.refresh(schedule)
        return schedule

    def delete(self, schedule: TrainerSchedule) -> None:
        """Удаление расписания"""
        self.db.delete(schedule)
        self.db.commit()

