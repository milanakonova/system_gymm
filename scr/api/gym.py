"""
API endpoints для входа/выхода из зала
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole
from scr.core.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/api/gym", tags=["gym"])


@router.post("/enter")
async def enter_gym(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Вход клиента в зал"""
    from scr.services.gym_service import GymService
    gym_service = GymService(db)
    return gym_service.enter_gym(current_user)


@router.post("/exit")
async def exit_gym(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Выход клиента из зала"""
    from scr.services.gym_service import GymService
    gym_service = GymService(db)
    return gym_service.exit_gym(current_user)


@router.get("/status")
async def get_gym_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Получение статуса клиента в зале"""
    from scr.services.gym_service import GymService
    gym_service = GymService(db)
    return gym_service.get_gym_status(current_user)

