"""
Сервис аутентификации
"""
from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from scr.core.security import verify_password, get_password_hash, create_access_token
from scr.core.config import settings
from scr.db.models import User
from scr.db.repositories.user_repository import UserRepository
from scr.schemas.user import UserCreate, Token


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        """Регистрация нового пользователя"""
        try:
            # Проверка существования пользователя
            if self.user_repo.get_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует"
                )
            
            if self.user_repo.get_by_phone(user_data.phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким телефоном уже существует"
                )

            # Создание пользователя
            hashed_password = get_password_hash(user_data.password)
            
            # Роль уже валидирована в схеме UserCreate
            user = User(
                email=user_data.email,
                phone=user_data.phone,
                password_hash=hashed_password,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                middle_name=user_data.middle_name,
                birth_date=user_data.birth_date,
                gender=user_data.gender,
                role=user_data.role
            )

            created_user = self.user_repo.create(user)
            print(f"Пользователь создан: {created_user.email}, ID: {created_user.id}")
            return created_user
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            print(f"Ошибка в AuthService.register: {str(e)}")
            print(traceback.format_exc())
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при регистрации: {str(e)}"
            )

    def login(self, email: str, password: str) -> Token:
        """Вход пользователя.

        Поддерживаем ввод:
        - email (admin@gym.com)
        - логин без домена (admin -> admin@gym.com)
        - телефон
        """
        identifier = (email or "").strip()
        identifier_l = identifier.lower()

        user = None
        # 1) Пробуем как email
        if identifier:
            user = self.user_repo.get_by_email(identifier_l)

        # 2) Если не нашли и это похоже на логин без домена — пробуем добавить домен проекта
        if not user and identifier and "@" not in identifier and not identifier.startswith("+") and not identifier.replace("-", "").replace(" ", "").isdigit():
            user = self.user_repo.get_by_email(f"{identifier_l}@gym.com")

        # 3) Пробуем как телефон (если ввели номер)
        if not user and identifier:
            user = self.user_repo.get_by_phone(identifier)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )

        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный email или пароль"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователь неактивен"
            )

        # Создание токена
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=access_token_expires
        )

        return Token(access_token=access_token)

