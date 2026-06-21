from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, ProgrammingError
from urllib.parse import urlparse
import time
from scr.db.models import Base


def ensure_database_exists(database_url: str) -> str:
    """
    Проверяет существование базы данных и создает её, если она не существует.
    
    :param database_url: Строка подключения к базе данных (например: postgresql://user:pass@host:port/dbname)
    :return: Строка подключения к базе данных (без изменений, если БД уже существует)
    """
    # Парсим URL для извлечения компонентов
    parsed = urlparse(database_url)
    
    # Извлекаем имя базы данных
    db_name = parsed.path.lstrip('/')
    
    if not db_name:
        raise ValueError("Имя базы данных не указано в DATABASE_URL")
    
    # Создаем URL для подключения к базе данных по умолчанию (postgres)
    default_db_url = f"{parsed.scheme}://{parsed.netloc}/postgres"
    
    print(f"Проверка существования базы данных '{db_name}'...")
    
    try:
        # Подключаемся к базе данных postgres (по умолчанию)
        default_engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
        
        with default_engine.connect() as conn:
            # Проверяем, существует ли база данных
            check_query = text(
                "SELECT 1 FROM pg_database WHERE datname = :db_name"
            )
            result = conn.execute(check_query, {"db_name": db_name})
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"База данных '{db_name}' не найдена. Создание...")
                # Создаем базу данных
                # В PostgreSQL нельзя использовать параметризованные запросы для CREATE DATABASE
                # Поэтому используем прямое форматирование (безопасно, т.к. db_name уже проверен)
                # Используем AUTOCOMMIT для немедленного применения изменений
                create_query = text(f'CREATE DATABASE "{db_name}"')
                conn.execute(create_query)
                # При использовании AUTOCOMMIT коммит не нужен, но даем время на обновление каталога
                time.sleep(0.5)  # Небольшая задержка для обновления системного каталога PostgreSQL
                print(f"✅ База данных '{db_name}' успешно создана!")
                print(f"   Примечание: Обновите список баз данных в pgAdmin (правый клик -> Refresh)")
            else:
                print(f"✅ База данных '{db_name}' уже существует.")
        
        # Закрываем соединение явно для применения изменений
        default_engine.dispose()
        
    except OperationalError as e:
        # Если не можем подключиться к PostgreSQL
        error_msg = str(e)
        if "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
            raise ConnectionError(
                f"Не удалось подключиться к PostgreSQL. "
                f"Убедитесь, что PostgreSQL запущен и доступен по адресу {parsed.hostname}:{parsed.port or 5432}"
            ) from e
        elif "password authentication failed" in error_msg.lower():
            raise ConnectionError(
                f"Ошибка аутентификации. Проверьте правильность имени пользователя и пароля."
            ) from e
        else:
            raise ConnectionError(f"Ошибка подключения к PostgreSQL: {e}") from e
    except ProgrammingError as e:
        # Если нет прав на создание базы данных
        error_msg = str(e)
        if "permission denied" in error_msg.lower() or "access denied" in error_msg.lower():
            raise PermissionError(
                f"Недостаточно прав для создания базы данных '{db_name}'. "
                f"Убедитесь, что пользователь имеет права CREATEDB."
            ) from e
        else:
            raise Exception(f"Ошибка при создании базы данных: {e}") from e
    except Exception as e:
        raise Exception(f"Неожиданная ошибка при проверке/создании базы данных: {e}") from e
    
    return database_url


def initialize_database(database_url: str):

    """
    Создает движок SQLAlchemy, инициализирует таблицы и добавляет начальные данные.

    :param database_url: Строка подключения к базе данных.
    """
    print("--- Начинается инициализация базы данных ---")
    try:
        # 0. Проверка и создание базы данных, если необходимо
        database_url = ensure_database_exists(database_url)
        
        # 1. Создание движка с явными настройками для видимости в pgAdmin
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            echo=False,
            # Убеждаемся, что изменения видны сразу
            isolation_level="READ COMMITTED"
        )
        print(f" Движок создан для URL: {database_url}")

        # 2. Создание таблиц с явным коммитом
        create_tables(engine)
        print(" Таблицы успешно созданы!")

        # 3. Инициализация начальных данных
        Session = sessionmaker(bind=engine)
        session = Session()
        try:
            init_default_data(session)
            print(" Начальные данные добавлены успешно!")
        except Exception as data_e:
            session.rollback()  # Откат при ошибке добавления данных
            print(f" Ошибка при добавлении начальных данных: {data_e}")
            raise  # Повторное возбуждение для внешнего try/except
        finally:
            session.close()

    except Exception as e:
        print(f" Критическая ошибка при создании/инициализации базы данных: {e}")
        # Завершаем программу при критической ошибке

    print("--- Инициализация базы данных успешно завершена ---")
# Функция для создания всех таблиц
def create_tables(engine):
    """Создание всех таблиц в базе данных"""
    from scr.db.models import Base
    # Создаем все таблицы
    # create_all автоматически создает таблицы и коммитит изменения
    # Используем begin() для явного управления транзакцией и гарантии видимости в pgAdmin
    with engine.begin() as conn:
        # Создаем все таблицы в явной транзакции для гарантии коммита
        Base.metadata.create_all(bind=conn)
        # Транзакция автоматически коммитится при выходе из блока


# Функция для создания сессии
def create_session(connection_string):
    """Создание сессии для работы с базой данных"""
    engine = create_engine(connection_string, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


# Функция для инициализации начальных данных
def init_default_data(session):
    """Добавление начальных данных в базу"""
    from scr.db.models import Service, GymZone, Locker
    from scr.core.security import get_password_hash
    from scr.db.models import User, UserRole
    
    # Создание администратора по умолчанию
    admin = session.query(User).filter(User.email == "admin@gym.com").first()
    if not admin:
        admin = User(
            email="admin@gym.com",
            phone="+79999999999",
            password_hash=get_password_hash("admin123"),
            first_name="Администратор",
            last_name="Системы",
            role=UserRole.ADMIN,
            is_active=True
        )
        session.add(admin)
    
    # Создание базовых залов (нужно для расписания тренеров и фильтрации)
    zones_data = [
        {"name": "Тренажерный зал", "description": "Основной зал с тренажерами", "capacity": 50},
        {"name": "Бассейн", "description": "Зона бассейна", "capacity": 20},
        {"name": "Зал групповых занятий", "description": "Зона для групповых тренировок", "capacity": 30},
    ]

    zones_by_name = {}
    for zone_data in zones_data:
        zone = session.query(GymZone).filter(GymZone.name == zone_data["name"]).first()
        if not zone:
            zone = GymZone(**zone_data)
            session.add(zone)
            session.flush()  # чтобы получить id
        zones_by_name[zone.name] = zone

    # Создание базовых услуг
    # (service_id обязателен для бронирования, поэтому держим хотя бы 1 услугу на каждый зал)
    services_data = [
        {"name": "Посещение тренажерного зала", "category": "gym", "duration_minutes": 120, "base_price": 500, "zone": "Тренажерный зал"},
        {"name": "Индивидуальная тренировка", "category": "training", "duration_minutes": 60, "base_price": 2000, "zone": "Тренажерный зал"},
        {"name": "Групповое занятие", "category": "group", "duration_minutes": 45, "base_price": 800, "zone": "Зал групповых занятий"},
        {"name": "Плавание", "category": "pool", "duration_minutes": 60, "base_price": 700, "zone": "Бассейн"},
    ]
    
    for service_data in services_data:
        zone_name = service_data.pop("zone", None)
        service = session.query(Service).filter(Service.name == service_data["name"]).first()
        if not service:
            if zone_name and zone_name in zones_by_name:
                service_data["gym_zone_id"] = zones_by_name[zone_name].id
            service = Service(**service_data)
            session.add(service)
        else:
            # если услуга уже есть, но зал не проставлен — проставим
            if zone_name and getattr(service, "gym_zone_id", None) is None and zone_name in zones_by_name:
                service.gym_zone_id = zones_by_name[zone_name].id
    
    # Создание базовых шкафчиков
    for i in range(1, 21):  # 20 шкафчиков
        locker = session.query(Locker).filter(Locker.locker_number == f"L{i:03d}").first()
        if not locker:
            import random
            locker = Locker(
                locker_number=f"L{i:03d}",
                zone="main",
                gender="men" if i <= 10 else "women",
                status="free",
                code=random.randint(1000, 9999),
                is_available=True
            )
            session.add(locker)
    
    session.commit()
    print("  - Создан администратор (admin@gym.com / admin123)")
    print("  - Созданы базовые залы и услуги")
    print("  - Созданы шкафчики")