"""
Скрипт для инициализации базы данных
Запустите этот файл для создания всех таблиц и начальных данных
"""
import sys
from scr.db.init_db import initialize_database
from scr.core.config import settings

if __name__ == "__main__":
    print("=" * 50)
    print("Инициализация базы данных")
    print("=" * 50)
    print(f"Подключение к: {settings.DATABASE_URL}")
    print()
    
    try:
        initialize_database(settings.DATABASE_URL)
        print()
        print("=" * 50)
        print("✅ Инициализация успешно завершена!")
        print("=" * 50)
        print()
        print("Данные для входа администратора:")
        print("  Email: admin@gym.com")
        print("  Password: admin123")
        print()
    except Exception as e:
        print()
        print("=" * 50)
        print("❌ Ошибка при инициализации базы данных")
        print("=" * 50)
        print(f"Ошибка: {e}")
        print()
        print("Проверьте:")
        print("  1. PostgreSQL запущен")
        print("  2. Пользователь 'postgres' имеет права CREATEDB (для автоматического создания БД)")
        print("  3. Пароль правильный (1234)")
        print("  4. База данных 'gym_sistem' будет создана автоматически, если её нет")
        sys.exit(1)

