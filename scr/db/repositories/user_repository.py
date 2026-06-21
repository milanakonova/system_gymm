"""
Репозиторий для работы с пользователями
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from scr.db.models import User, UserRole


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        """Создание пользователя"""
        try:
            self.db.add(user)
            self.db.commit()  # Коммитим транзакцию
            self.db.refresh(user)
            print(f"Пользователь создан в БД: {user.email}, ID: {user.id}")
            return user
        except Exception as e:
            import traceback
            print(f"Ошибка в UserRepository.create: {str(e)}")
            print(traceback.format_exc())
            self.db.rollback()
            raise e

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Получение пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_phone(self, phone: str) -> Optional[User]:
        """Получение пользователя по телефону"""
        return self.db.query(User).filter(User.phone == phone).first()

    def get_all(self, role: Optional[UserRole] = None, is_active: Optional[bool] = None) -> List[User]:
        """Получение всех пользователей с фильтрацией"""
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.all()

    def search(self, search_term: str) -> List[User]:
        """Поиск пользователей"""
        search_pattern = f"%{search_term}%"
        return self.db.query(User).filter(
            or_(
                User.first_name.ilike(search_pattern),
                User.last_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
                User.phone.ilike(search_pattern)
            )
        ).all()

    def update(self, user: User) -> User:
        """Обновление пользователя"""
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """Удаление пользователя"""
        self.db.delete(user)
        self.db.commit()

