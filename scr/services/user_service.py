"""
Сервис для работы с пользователями
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from scr.db.models import User, UserRole
from scr.db.repositories.user_repository import UserRepository
from scr.schemas.user import UserCreate, UserUpdate
from scr.core.security import get_password_hash


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def create_user(self, user_data: UserCreate, created_by: Optional[User] = None) -> User:
        """Создание пользователя (только для администраторов)"""
        # Проверка существования
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

        return self.user_repo.create(user)

    def get_user(self, user_id: UUID) -> User:
        """Получение пользователя по ID"""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пользователь не найден"
            )
        return user

    def get_users(
        self,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Получение списка пользователей с фильтрацией"""
        users = self.user_repo.get_all(role=role, is_active=is_active)
        return users[skip:skip + limit]

    def search_users(self, search_term: str) -> List[User]:
        """Поиск пользователей"""
        return self.user_repo.search(search_term)

    def update_user(self, user_id: UUID, user_data: UserUpdate, current_user: User) -> User:
        """Обновление пользователя"""
        user = self.get_user(user_id)

        # Проверка прав: пользователь может обновлять только свой профиль,
        # администратор может обновлять любого
        if current_user.role != UserRole.ADMIN and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для обновления этого пользователя"
            )

        # Проверка уникальности email
        if user_data.email and user_data.email != user.email:
            if self.user_repo.get_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует"
                )
            user.email = user_data.email

        # Проверка уникальности телефона
        if user_data.phone and user_data.phone != user.phone:
            if self.user_repo.get_by_phone(user_data.phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким телефоном уже существует"
                )
            user.phone = user_data.phone

        # Обновление остальных полей
        update_data = user_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        return self.user_repo.update(user)

    def delete_user(self, user_id: UUID, current_user: User) -> None:
        """Удаление пользователя (только администратор)"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может удалять пользователей"
            )

        user = self.get_user(user_id)
        
        # Нельзя удалить самого себя
        if user.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить самого себя"
            )

        self.user_repo.delete(user)

    def deactivate_user(self, user_id: UUID, current_user: User) -> User:
        """Деактивация пользователя"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может деактивировать пользователей"
            )

        user = self.get_user(user_id)
        user.is_active = False
        return self.user_repo.update(user)

    def activate_user(self, user_id: UUID, current_user: User) -> User:
        """Активация пользователя"""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только администратор может активировать пользователей"
            )

        user = self.get_user(user_id)
        user.is_active = True
        return self.user_repo.update(user)

