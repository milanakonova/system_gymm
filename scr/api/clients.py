"""
API endpoints для клиентов
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole
from scr.core.dependencies import get_current_active_user, require_role
from scr.services.gym_service import GymService
from scr.services.contract_service import ContractService

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("/me")
async def get_client_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Получение информации о текущем клиенте"""
    gym_service = GymService(db)
    contract_service = ContractService(db)
    
    # Получаем статус в зале
    gym_status = gym_service.get_gym_status(current_user)
    
    # Получаем активные абонементы
    active_subscriptions = contract_service.get_client_active_subscriptions(current_user.id, current_user)
    
    has_subscription = len(active_subscriptions) > 0
    visits_left = gym_status.get("visits_remaining", 0)
    
    return {
        "visits_left": visits_left,
        "has_subscription": has_subscription,
        "in_gym": gym_status.get("in_gym", False),
        "active_subscriptions_count": len(active_subscriptions)
    }


@router.post("/me/check-in")
async def client_check_in(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    """Отметка посещения клиентом"""
    gym_service = GymService(db)
    result = gym_service.enter_gym(current_user)
    
    # Обновляем информацию о посещениях
    contract_service = ContractService(db)
    gym_status = gym_service.get_gym_status(current_user)
    
    return {
        "message": result.get("message", "Посещение отмечено"),
        "visits_left": gym_status.get("visits_remaining", 0),
        "in_gym": True
    }

