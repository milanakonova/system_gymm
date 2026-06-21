"""
API endpoints для управления пользователями
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole
from scr.schemas.user import UserCreate, UserUpdate, UserResponse
from scr.services.user_service import UserService
from scr.core.dependencies import get_current_active_user, require_role

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Создание нового пользователя (только администратор)"""
    user_service = UserService(db)
    return user_service.create_user(user_data, current_user)


@router.get("", response_model=List[UserResponse])
async def get_users(
    role: Optional[UserRole] = Query(None, description="Фильтр по роли"),
    is_active: Optional[bool] = Query(None, description="Фильтр по активности"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Получение списка пользователей (только администратор)"""
    user_service = UserService(db)
    return user_service.get_users(role=role, is_active=is_active, skip=skip, limit=limit)


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=1, description="Поисковый запрос"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Поиск пользователей (только администратор)"""
    user_service = UserService(db)
    return user_service.search_users(q)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о пользователе"""
    user_service = UserService(db)
    
    # Пользователь может видеть только свой профиль, администратор - любой
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для просмотра этого пользователя"
        )
    
    return user_service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновление пользователя"""
    user_service = UserService(db)
    return user_service.update_user(user_id, user_data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Удаление пользователя (только администратор)"""
    user_service = UserService(db)
    user_service.delete_user(user_id, current_user)
    return None


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Деактивация пользователя (только администратор)"""
    user_service = UserService(db)
    return user_service.deactivate_user(user_id, current_user)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Активация пользователя (только администратор)"""
    user_service = UserService(db)
    return user_service.activate_user(user_id, current_user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о текущем пользователе"""
    return current_user

