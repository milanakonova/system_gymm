"""
API endpoints для управления расписанием тренеров
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime, time
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole, TrainerSchedule, Booking, BookingStatus
from scr.schemas.trainer_schedule import (
    TrainerScheduleCreate,
    TrainerScheduleUpdate,
    TrainerScheduleResponse
)
from scr.services.trainer_service import TrainerService
from scr.core.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/api/trainer", tags=["trainer"])


@router.post("/schedule", response_model=TrainerScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: TrainerScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.TRAINER))
):
    """Создание записи расписания (только тренер)"""
    trainer_service = TrainerService(db)
    return trainer_service.create_schedule(schedule_data, current_user)


@router.get("/schedule", response_model=List[TrainerScheduleResponse])
async def get_schedules(
    trainer_id: Optional[UUID] = Query(None, description="ID тренера"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение расписания тренера"""
    trainer_service = TrainerService(db)
    target_trainer_id = trainer_id if trainer_id else current_user.id
    return trainer_service.get_trainer_schedules(target_trainer_id, current_user)


@router.get("/schedule/{schedule_id}", response_model=TrainerScheduleResponse)
async def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение записи расписания"""
    trainer_service = TrainerService(db)
    return trainer_service.get_schedule(schedule_id, current_user)


@router.put("/schedule/{schedule_id}", response_model=TrainerScheduleResponse)
async def update_schedule(
    schedule_id: int,
    schedule_data: TrainerScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновление расписания"""
    trainer_service = TrainerService(db)
    return trainer_service.update_schedule(schedule_id, schedule_data, current_user)


@router.post("/schedule/{schedule_id}/cancel", response_model=TrainerScheduleResponse)
async def cancel_schedule(
    schedule_id: int,
    reason: str = Query(..., description="Причина отмены"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Отмена тренировки (только тренер)"""
    trainer_service = TrainerService(db)
    return trainer_service.cancel_schedule(schedule_id, reason, current_user)


@router.delete("/schedule/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Удаление расписания"""
    trainer_service = TrainerService(db)
    trainer_service.delete_schedule(schedule_id, current_user)
    return None


@router.get("/schedule/available", response_model=List[TrainerScheduleResponse])
async def get_available_schedules(
    trainer_id: UUID = Query(..., description="ID тренера"),
    day_of_week: Optional[int] = Query(None, ge=0, le=6, description="День недели (0-6)"),
    db: Session = Depends(get_db)
):
    """Получение доступного расписания тренера (публичный endpoint)"""
    trainer_service = TrainerService(db)
    return trainer_service.get_available_schedules(trainer_id, day_of_week)


@router.get("/schedule/trainer/{trainer_id}", response_model=List[TrainerScheduleResponse])
async def get_trainer_schedule_by_id(
    trainer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение расписания тренера по ID"""
    trainer_service = TrainerService(db)
    return trainer_service.get_trainer_schedules(trainer_id, current_user)


@router.get("/schedule/available-slots")
async def get_available_time_slots(
    booking_date: date = Query(..., description="Дата для бронирования"),
    gym_zone_id: Optional[int] = Query(None, description="ID зала (опционально)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение доступных временных слотов для записи"""
    # Получаем день недели для выбранной даты
    day_of_week = booking_date.weekday()
    
    # Получаем все доступные расписания на этот день недели
    query = db.query(TrainerSchedule).filter(
        TrainerSchedule.day_of_week == day_of_week,
        TrainerSchedule.is_working == True,
        TrainerSchedule.is_cancelled == False
    )
    
    if gym_zone_id:
        if hasattr(TrainerSchedule, 'gym_zone_id'):
            query = query.filter(TrainerSchedule.gym_zone_id == gym_zone_id)
    
    schedules = query.all()
    
    # Получаем существующие бронирования на эту дату
    existing_bookings = db.query(Booking).filter(
        Booking.booking_date == booking_date,
        Booking.status != BookingStatus.CANCELLED
    ).all()
    
    # Формируем список доступных слотов
    available_slots = []
    for schedule in schedules:
        # Проверяем, не занят ли этот слот
        is_booked = any(
            booking.trainer_schedule_id == schedule.id
            for booking in existing_bookings
        )
        
        if not is_booked:
            # Получаем информацию о тренере
            trainer = db.query(User).filter(User.id == schedule.trainer_id).first()
            trainer_name = f"{trainer.first_name} {trainer.last_name}" if trainer else "Тренер"
            
            # Получаем информацию о зале
            zone_name = "Не указан"
            if hasattr(schedule, 'gym_zone_id') and schedule.gym_zone_id:
                from scr.db.models import GymZone
                zone = db.query(GymZone).filter(GymZone.id == schedule.gym_zone_id).first()
                if zone:
                    zone_name = zone.name
            
            available_slots.append({
                "schedule_id": schedule.id,
                "trainer_id": str(schedule.trainer_id),
                "trainer_name": trainer_name,
                "start_time": schedule.start_time.strftime("%H:%M"),
                "end_time": schedule.end_time.strftime("%H:%M"),
                "zone_id": schedule.gym_zone_id if hasattr(schedule, 'gym_zone_id') else None,
                "zone_name": zone_name
            })
    
    return {"slots": available_slots, "date": booking_date.isoformat()}
