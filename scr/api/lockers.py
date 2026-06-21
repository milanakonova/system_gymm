"""
API endpoints для управления шкафчиками
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole
from scr.schemas.locker import LockerResponse
from scr.services.locker_service import LockerService
from scr.core.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/api/lockers", tags=["lockers"])


@router.get("", response_model=List[LockerResponse])
async def get_lockers(
    gender: Optional[str] = Query(None, description="Фильтр по полу (men/women)"),
    status: Optional[str] = Query(None, description="Фильтр по статусу (free/occupied)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Получение списка шкафчиков (только администратор)"""
    from scr.db.repositories.locker_repository import LockerRepository
    locker_repo = LockerRepository(db)
    return locker_repo.get_all(gender=gender, status=status)


@router.get("/available", response_model=List[LockerResponse])
async def get_available_lockers(
    gender: str = Query(..., description="Пол (men/women)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение доступных шкафчиков"""
    from scr.db.repositories.locker_repository import LockerRepository
    locker_repo = LockerRepository(db)
    return locker_repo.get_available(gender)


@router.get("/my", response_model=Optional[LockerResponse])
async def get_my_locker(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Получение шкафчика текущего клиента"""
    locker_service = LockerService(db)
    locker = locker_service.get_user_locker(current_user.id)
    if locker:
        return locker
    return None


@router.post("/{locker_id}/release", response_model=LockerResponse)
async def release_locker(
    locker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Освобождение шкафчика"""
    locker_service = LockerService(db)
    
    # Проверяем, что шкафчик принадлежит клиенту
    locker = locker_service.get_user_locker(current_user.id)
    if not locker or locker.id != locker_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Этот шкафчик не принадлежит вам"
        )
    
    return locker_service.release_locker(locker_id)

