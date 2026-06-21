"""
API endpoints для аутентификации
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.schemas.user import UserCreate, UserResponse, UserLogin, Token
from scr.services.auth_service import AuthService
from scr.core.dependencies import get_current_active_user
from scr.db.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Регистрация нового пользователя"""
    try:
        auth_service = AuthService(db)
        user = auth_service.register(user_data)
        # Коммит уже выполнен в репозитории
        return user
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"Ошибка при регистрации: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при регистрации: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """Вход пользователя"""
    auth_service = AuthService(db)
    token = auth_service.login(credentials.email, credentials.password)
    return token


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о текущем пользователе"""
    return current_user

