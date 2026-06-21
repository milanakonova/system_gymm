"""
Pydantic схемы для пользователей
"""
from typing import Optional, Union
from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator

from scr.db.models import UserRole


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    email: EmailStr
    phone: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    role: UserRole = UserRole.CLIENT
    
    @field_validator('role', mode='before')
    @classmethod
    def validate_role(cls, v):
        """Валидация и преобразование роли"""
        if isinstance(v, str):
            v = v.lower()
            try:
                return UserRole(v)
            except ValueError:
                return UserRole.CLIENT
        return v


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    password: str


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None
    photo_url: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя"""
    id: UUID
    is_active: bool
    in_gym: bool
    current_locker_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Схема для входа"""
    # Разрешаем ввод не только email (например: "admin" или телефон),
    # иначе FastAPI отдаст 422 и вход "ломается".
    email: str
    password: str


class Token(BaseModel):
    """Схема токена"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные токена"""
    user_id: Optional[UUID] = None

