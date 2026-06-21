"""
Сервис для работы с бронированиями
"""
from typing import List, Optional
from uuid import UUID
from datetime import date, time
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from scr.db.models import (
    Booking, BookingStatus, User, UserRole,
    TrainerSchedule, Service, Subscription
)
from scr.db.repositories.booking_repository import BookingRepository
from scr.db.repositories.trainer_schedule_repository import TrainerScheduleRepository
from scr.db.repositories.subscription_repository import SubscriptionRepository
from scr.schemas.booking import BookingCreate, BookingUpdate
from scr.services.contract_service import ContractService


class BookingService:
    def __init__(self, db: Session):
        self.db = db
        self.booking_repo = BookingRepository(db)
        self.schedule_repo = TrainerScheduleRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.contract_service = ContractService(db)

    def create_booking(
        self,
        booking_data: BookingCreate,
        current_user: User,
        client_id: Optional[UUID] = None
    ) -> Booking:
        """
        Создание бронирования
        client_id - для администратора, который записывает клиента
        """
        # Определяем клиента
        if client_id:
            # Администратор записывает клиента
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Только администратор может записывать других клиентов"
                )
            target_client_id = client_id
        else:
            # Клиент записывает себя
            if current_user.role != UserRole.CLIENT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Только клиенты могут создавать бронирования"
                )
            target_client_id = current_user.id

        # Проверка существования услуги
        service = self.db.query(Service).filter(Service.id == booking_data.service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Услуга не найдена"
            )

        # Проверка абонемента, если указан
        subscription = None
        if booking_data.subscription_id:
            subscription = self.subscription_repo.get_by_id(booking_data.subscription_id)
            if not subscription:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Абонемент не найден"
                )
            if subscription.contract.client_id != target_client_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Абонемент принадлежит другому клиенту"
                )

        # Проверка расписания тренера, если указано
        trainer_schedule = None
        if booking_data.trainer_schedule_id:
            trainer_schedule = self.schedule_repo.get_by_id(booking_data.trainer_schedule_id)
            if not trainer_schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Расписание тренера не найдено"
                )
            if trainer_schedule.is_cancelled or not trainer_schedule.is_working:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Расписание тренера недоступно"
                )

        # Проверка конфликтов
        conflicts = self.booking_repo.get_conflicting_bookings(
            booking_data.booking_date,
            booking_data.start_time,
            booking_data.end_time,
            booking_data.trainer_schedule_id
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Время уже занято"
            )

        # Создание бронирования
        booking = Booking(
            client_id=target_client_id,
            subscription_id=booking_data.subscription_id,
            service_id=booking_data.service_id,
            trainer_schedule_id=booking_data.trainer_schedule_id,
            booking_date=booking_data.booking_date,
            start_time=booking_data.start_time,
            end_time=booking_data.end_time,
            status=BookingStatus.CONFIRMED,
            notes=booking_data.notes
        )

        return self.booking_repo.create(booking)

    def get_booking(self, booking_id: UUID, current_user: User) -> Booking:
        """Получение бронирования"""
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Бронирование не найдено"
            )

        # Клиент может видеть только свои бронирования
        if current_user.role == UserRole.CLIENT and booking.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        return booking

    def get_client_bookings(
        self,
        client_id: UUID,
        current_user: User,
        status_filter: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получение бронирований клиента"""
        # Клиент может видеть только свои бронирования
        if current_user.role == UserRole.CLIENT and client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        if status_filter:
            return self.booking_repo.get_all(client_id=client_id, status=status_filter)
        return self.booking_repo.get_by_client_id(client_id)

    def cancel_booking(self, booking_id: UUID, current_user: User) -> Booking:
        """Отмена бронирования"""
        booking = self.get_booking(booking_id, current_user)

        # Клиент может отменять только свои бронирования
        if current_user.role == UserRole.CLIENT and booking.client_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав"
            )

        if booking.status == BookingStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Бронирование уже отменено"
            )

        booking.status = BookingStatus.CANCELLED
        return self.booking_repo.update(booking)

    def get_available_slots(
        self,
        service_id: int,
        booking_date: date,
        trainer_id: Optional[UUID] = None
    ) -> List[dict]:
        """Получение доступных слотов для бронирования"""
        service = self.db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Услуга не найдена"
            )

        # Получаем расписание тренеров
        if trainer_id:
            schedules = self.schedule_repo.get_available_schedules(
                trainer_id,
                day_of_week=booking_date.weekday()
            )
        else:
            # Все доступные расписания
            schedules = self.schedule_repo.get_all(is_working=True)
            schedules = [s for s in schedules if s.day_of_week == booking_date.weekday()]

        available_slots = []
        for schedule in schedules:
            # Проверяем занятость
            conflicts = self.booking_repo.get_conflicting_bookings(
                booking_date,
                schedule.start_time,
                schedule.end_time,
                schedule.id
            )
            if not conflicts:
                available_slots.append({
                    "trainer_schedule_id": schedule.id,
                    "trainer_id": schedule.trainer_id,
                    "start_time": schedule.start_time,
                    "end_time": schedule.end_time
                })

        return available_slots

