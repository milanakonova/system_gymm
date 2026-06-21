"""
API endpoints для управления бронированиями
"""
from typing import List, Optional
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole, BookingStatus
from scr.schemas.booking import BookingCreate, BookingUpdate, BookingResponse, BookingWithDetails
from scr.services.booking_service import BookingService
from scr.core.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    booking_data: BookingCreate,
    client_id: Optional[UUID] = Query(None, description="ID клиента (только для администратора)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создание бронирования"""
    booking_service = BookingService(db)
    return booking_service.create_booking(booking_data, current_user, client_id)


@router.get("", response_model=List[BookingResponse])
async def get_bookings(
    client_id: Optional[UUID] = Query(None, description="ID клиента"),
    status_filter: Optional[BookingStatus] = Query(None, description="Фильтр по статусу"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка бронирований"""
    booking_service = BookingService(db)
    if client_id:
        return booking_service.get_client_bookings(client_id, current_user, status_filter)
    # Клиент видит только свои бронирования
    if current_user.role == UserRole.CLIENT:
        return booking_service.get_client_bookings(current_user.id, current_user, status_filter)
    # Администратор видит все
    from scr.db.repositories.booking_repository import BookingRepository
    repo = BookingRepository(db)
    return repo.get_all(status=status_filter)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение бронирования"""
    booking_service = BookingService(db)
    return booking_service.get_booking(booking_id, current_user)


@router.delete("/{booking_id}", response_model=BookingResponse)
async def cancel_booking(
    booking_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Отмена бронирования"""
    booking_service = BookingService(db)
    return booking_service.cancel_booking(booking_id, current_user)


@router.get("/available/slots", response_model=List[dict])
async def get_available_slots(
    service_id: int = Query(..., description="ID услуги"),
    booking_date: date = Query(..., description="Дата бронирования"),
    trainer_id: Optional[UUID] = Query(None, description="ID тренера (опционально)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение доступных слотов для бронирования"""
    booking_service = BookingService(db)
    return booking_service.get_available_slots(service_id, booking_date, trainer_id)

