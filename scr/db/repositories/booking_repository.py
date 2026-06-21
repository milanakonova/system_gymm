"""
Репозиторий для работы с бронированиями
"""
from typing import Optional, List
from uuid import UUID
from datetime import date, time
from sqlalchemy.orm import Session

from scr.db.models import Booking, BookingStatus


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking: Booking) -> Booking:
        """Создание бронирования"""
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get_by_id(self, booking_id: UUID) -> Optional[Booking]:
        """Получение бронирования по ID"""
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_by_client_id(self, client_id: UUID) -> List[Booking]:
        """Получение всех бронирований клиента"""
        return self.db.query(Booking).filter(Booking.client_id == client_id).all()

    def get_by_trainer_schedule_id(self, trainer_schedule_id: int) -> List[Booking]:
        """Получение всех бронирований для расписания тренера"""
        return self.db.query(Booking).filter(
            Booking.trainer_schedule_id == trainer_schedule_id
        ).all()

    def get_by_date_range(
        self,
        start_date: date,
        end_date: date,
        service_id: Optional[int] = None
    ) -> List[Booking]:
        """Получение бронирований за период"""
        query = self.db.query(Booking).filter(
            Booking.booking_date >= start_date,
            Booking.booking_date <= end_date,
            Booking.status == BookingStatus.CONFIRMED
        )
        if service_id:
            query = query.filter(Booking.service_id == service_id)
        return query.all()

    def get_conflicting_bookings(
        self,
        booking_date: date,
        start_time: time,
        end_time: time,
        trainer_schedule_id: Optional[int] = None,
        exclude_booking_id: Optional[UUID] = None
    ) -> List[Booking]:
        """Проверка конфликтов бронирований"""
        query = self.db.query(Booking).filter(
            Booking.booking_date == booking_date,
            Booking.status == BookingStatus.CONFIRMED,
            # Проверка пересечения времени
            Booking.start_time < end_time,
            Booking.end_time > start_time
        )
        if trainer_schedule_id:
            query = query.filter(Booking.trainer_schedule_id == trainer_schedule_id)
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
        return query.all()

    def get_all(
        self,
        client_id: Optional[UUID] = None,
        service_id: Optional[int] = None,
        status: Optional[BookingStatus] = None
    ) -> List[Booking]:
        """Получение всех бронирований с фильтрацией"""
        query = self.db.query(Booking)
        if client_id:
            query = query.filter(Booking.client_id == client_id)
        if service_id:
            query = query.filter(Booking.service_id == service_id)
        if status:
            query = query.filter(Booking.status == status)
        return query.all()

    def update(self, booking: Booking) -> Booking:
        """Обновление бронирования"""
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def delete(self, booking: Booking) -> None:
        """Удаление бронирования"""
        self.db.delete(booking)
        self.db.commit()

