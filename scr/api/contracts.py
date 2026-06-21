"""
API endpoints для управления контрактами и абонементами
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User
from scr.schemas.contract import ContractCreate, ContractUpdate, ContractResponse, ContractWithSubscriptions
from scr.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from scr.services.contract_service import ContractService
from scr.core.dependencies import get_current_active_user, require_role
from scr.db.models import UserRole

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Создание нового контракта (только администратор)"""
    contract_service = ContractService(db)
    return contract_service.create_contract(contract_data, current_user)


@router.get("", response_model=List[ContractResponse])
async def get_contracts(
    client_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение списка контрактов"""
    contract_service = ContractService(db)
    if client_id:
        return contract_service.get_client_contracts(client_id, current_user)
    # Администратор может видеть все контракты
    if current_user.role == UserRole.ADMIN:
        from scr.db.repositories.contract_repository import ContractRepository
        repo = ContractRepository(db)
        return repo.get_all()
    # Клиент видит только свои
    return contract_service.get_client_contracts(current_user.id, current_user)


@router.get("/{contract_id}", response_model=ContractWithSubscriptions)
async def get_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение контракта с абонементами"""
    contract_service = ContractService(db)
    return contract_service.get_contract(contract_id, current_user)


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Обновление контракта (только администратор)"""
    contract_service = ContractService(db)
    return contract_service.update_contract(contract_id, contract_data, current_user)


@router.post("/{contract_id}/activate", response_model=ContractResponse)
async def activate_contract(
    contract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Активация контракта (только администратор)"""
    contract_service = ContractService(db)
    return contract_service.activate_contract(contract_id, current_user)


@router.post("/{contract_id}/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    contract_id: UUID,
    subscription_data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Создание абонемента для контракта (только администратор)"""
    contract_service = ContractService(db)
    return contract_service.create_subscription(contract_id, subscription_data, current_user)


@router.get("/clients/{client_id}/subscriptions/active", response_model=List[SubscriptionResponse])
async def get_client_active_subscriptions(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение активных абонементов клиента"""
    contract_service = ContractService(db)
    return contract_service.get_client_active_subscriptions(client_id, current_user)

