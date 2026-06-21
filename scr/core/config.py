"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv

class Settings(BaseSettings):
    """Настройки приложения"""
    load_dotenv()
    # Название приложения
    APP_NAME: str = "Gym Management System"
    APP_VERSION: str = "1.0.0"
    
    # База данных
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DB_USERNAME: str = os.getenv("DB_USERNAME")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_DATABASE: str = os.getenv("DB_DATABASE")
    
    # JWT настройки
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    # Yookassa
    CONFIGURATION_SHOP_KEY: str
    CONFIGURATION_SECRET_KEY: str
    PAYMENT_RETURN_URL: str

    # Цены
    PRICE_GYM: int
    PRICE_GROUP: int
    PRICE_POOL: int
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

