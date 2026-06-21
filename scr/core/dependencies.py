"""
Зависимости FastAPI
"""
from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from scr.db.database import get_db
from scr.core.security import decode_access_token
from scr.db.models import User, UserRole
from scr.db.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Получение текущего пользователя из JWT токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    
    from uuid import UUID
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Проверка активности пользователя"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Неактивный пользователь")
    return current_user


def require_role(*allowed_roles: UserRole):
    """Декоратор для проверки роли пользователя"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав доступа"
            )
        return current_user
    return role_checker

