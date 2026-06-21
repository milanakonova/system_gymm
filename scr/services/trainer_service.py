"""
Сервис для работы с расписанием тренеров
"""
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from scr.db.models import TrainerSchedule, User, UserRole
from scr.db.repositories.trainer_schedule_repository import TrainerScheduleRepository
from scr.schemas.trainer_schedule import TrainerScheduleCreate, TrainerScheduleUpdate


class TrainerService:
    def __init__(self, db: Session):
        self.db = db
        self.schedule_repo = TrainerScheduleRepository(db)

    def create_schedule(
        self,
        schedule_data: TrainerScheduleCreate,
        current_user: User
    ) -> TrainerSchedule:
        """Создание записи расписания"""
        # Только тренер может создавать свое расписание
        if current_user.role != UserRole.TRAINER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только тренер может создавать расписание"
            )

        # Тренер может создавать расписание только для себя
        if schedule_data.trainer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Тренер может создавать расписание только для себя"
            )

        # Проверка валидности времени
        if schedule_data.start_time >= schedule_data.end_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Время начала должно быть меньше времени окончания"
            )

        # Проверка валидности дня недели
        if schedule_data.day_of_week < 0 or schedule_data.day_of_week > 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="День недели должен быть от 0 до 6"
            )

        schedule = TrainerSchedule(
            trainer_id=schedule_data.trainer_id,
            day_of_week=schedule_data.day_of_week,
            start_time=schedule_data.start_time,
            end_time=schedule_data.end_time,
            is_working=schedule_data.is_working,
            gym_zone_id=schedule_data.gym_zone_id if hasattr(schedule_data, 'gym_zone_id') else None
        )

        return self.schedule_repo.create(schedule)

    def get_schedule(self, schedule_id: int, current_user: User) -> TrainerSchedule:
        """Получение расписания"""
        schedule = self.schedule_repo.get_by_id(schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Расписание не найдено"
            )

        # Тренер может видеть только свое расписание
        if current_user.role == UserRole.TRAINER and schedule.trainer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return schedule

    def get_trainer_schedules(
        self,
        trainer_id: UUID,
        current_user: User
    ) -> List[TrainerSchedule]:
        """Получение расписания тренера"""
        # Тренер может видеть только свое расписание
        if current_user.role == UserRole.TRAINER and trainer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return self.schedule_repo.get_by_trainer_id(trainer_id)

    def update_schedule(
        self,
        schedule_id: int,
        schedule_data: TrainerScheduleUpdate,
        current_user: User
    ) -> TrainerSchedule:
        """Обновление расписания"""
        schedule = self.get_schedule(schedule_id, current_user)

        # Тренер может обновлять только свое расписание
        if current_user.role == UserRole.TRAINER and schedule.trainer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        update_data = schedule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)

        # Если отменяем, устанавливаем время отмены
        if schedule_data.is_cancelled and not schedule.is_cancelled:
            schedule.cancelled_at = datetime.now(timezone.utc)

        return self.schedule_repo.update(schedule)

    def cancel_schedule(
        self,
        schedule_id: int,
        reason: str,
        current_user: User
    ) -> TrainerSchedule:
        """Отмена расписания (тренировки)"""
        schedule = self.get_schedule(schedule_id, current_user)

        # Тренер может отменять только свое расписание
        if current_user.role == UserRole.TRAINER and schedule.trainer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        schedule.is_cancelled = True
        schedule.cancelled_at = datetime.now(timezone.utc)
        schedule.cancellation_reason = reason

        return self.schedule_repo.update(schedule)

    def delete_schedule(self, schedule_id: int, current_user: User) -> None:
        """Удаление расписания"""
        schedule = self.get_schedule(schedule_id, current_user)

        # Тренер может удалять только свое расписание
        if current_user.role == UserRole.TRAINER and schedule.trainer_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        self.schedule_repo.delete(schedule)

    def get_available_schedules(
        self,
        trainer_id: UUID,
        day_of_week: int = None
    ) -> List[TrainerSchedule]:
        """Получение доступного расписания тренера (публичный метод)"""
        return self.schedule_repo.get_available_schedules(trainer_id, day_of_week)

