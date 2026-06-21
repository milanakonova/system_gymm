"""
SQLAlchemy модели базы данных
"""
from datetime import datetime, date, time, timezone
import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Time, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# --- Перечисления (Enums) ---

class UserRole(PyEnum):
    CLIENT = "client"
    TRAINER = "trainer"
    ADMIN = "admin"


class ContractStatus(PyEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    EXPIRED = "expired"


class PaymentStatus(PyEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"


class SubscriptionType(PyEnum):
    TIME_BASED = "time_based"
    VISIT_BASED = "visit_based"


class BookingStatus(PyEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


# --- Основные таблицы ---

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    birth_date = Column(Date)
    gender = Column(String(10))  # "male" or "female"
    photo_url = Column(String(500))

    role = Column(Enum(UserRole), nullable=False, default=UserRole.CLIENT)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Дополнительные поля для клиентов
    in_gym = Column(Boolean, default=False)  # Находится ли клиент в зале
    current_locker_id = Column(Integer, ForeignKey('lockers.id', ondelete='SET NULL'), nullable=True)

    contracts = relationship("Contract", back_populates="client", cascade="all, delete-orphan")
    # В Visit теперь две ссылки на users (client_id и trainer_id),
    # поэтому явно указываем по какому FK строится связь.
    visits = relationship(
        "Visit",
        back_populates="client",
        cascade="all, delete-orphan",
        foreign_keys="Visit.client_id",
    )
    trainer_visits = relationship(
        "Visit",
        back_populates="trainer",
        foreign_keys="Visit.trainer_id",
    )
    payments = relationship("Payment", back_populates="client", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="client", cascade="all, delete-orphan")
    schedules = relationship("TrainerSchedule", back_populates="trainer_user")
    current_locker = relationship("Locker", foreign_keys=[current_locker_id])


class Service(Base):
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)
    max_participants = Column(Integer, default=1)
    base_price = Column(Float, nullable=False, default=0.0)

    # Привязка услуги к зоне (опционально)
    gym_zone_id = Column(Integer, ForeignKey('gym_zones.id', ondelete='SET NULL'))

    gym_zone = relationship("GymZone", back_populates="services")
    subscriptions = relationship("Subscription", back_populates="service")
    visits = relationship("Visit", back_populates="service")
    bookings = relationship("Booking", back_populates="service")


class GymZone(Base):
    __tablename__ = 'gym_zones'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    capacity = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)

    services = relationship("Service", back_populates="gym_zone")


class TrainerSchedule(Base):
    __tablename__ = 'trainer_schedules'
    id = Column(Integer, primary_key=True)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0-6 (понедельник-воскресенье)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_working = Column(Boolean, default=True)
    is_cancelled = Column(Boolean, default=False)  # Отменено ли занятие
    cancelled_at = Column(DateTime, nullable=True)  # Когда отменено
    cancellation_reason = Column(Text, nullable=True)  # Причина отмены
    gym_zone_id = Column(Integer, ForeignKey('gym_zones.id', ondelete='SET NULL'), nullable=True)  # ID зала

    trainer_user = relationship("User", back_populates="schedules")
    bookings = relationship("Booking", back_populates="trainer_schedule")
    gym_zone = relationship("GymZone")


# --- Разовые записи расписания (по конкретной дате) ---

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    gym_zone_id = Column(Integer, ForeignKey("gym_zones.id", ondelete="SET NULL"), nullable=True)

    session_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    is_cancelled = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    cancellation_reason = Column(Text, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trainer = relationship("User")
    gym_zone = relationship("GymZone")
    participants = relationship("TrainingSessionParticipant", back_populates="session", cascade="all, delete-orphan")


class TrainingSessionParticipant(Base):
    __tablename__ = "training_session_participants"

    session_id = Column(UUID(as_uuid=True), ForeignKey("training_sessions.id", ondelete="CASCADE"), primary_key=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("TrainingSession", back_populates="participants")
    client = relationship("User")


# --- Абонементы по залам (упрощенная модель без оплаты) ---

class ZonePass(Base):
    __tablename__ = "zone_passes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gym_zone_id = Column(Integer, ForeignKey("gym_zones.id", ondelete="CASCADE"), nullable=False)
    remaining_visits = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    client = relationship("User")
    gym_zone = relationship("GymZone")


class Contract(Base):
    __tablename__ = 'contracts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contract_number = Column(String(50), unique=True, nullable=False)
    status = Column(Enum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    signed_at = Column(DateTime)
    signed_by_client = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("User", back_populates="contracts")
    subscriptions = relationship("Subscription", back_populates="contract", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="contract")


class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id', ondelete='CASCADE'), nullable=False)
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    subscription_type = Column(Enum(SubscriptionType), nullable=False)
    total_visits = Column(Integer)  # Для VISIT_BASED
    remaining_visits = Column(Integer)  # Для VISIT_BASED
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)  # Для TIME_BASED
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    contract = relationship("Contract", back_populates="subscriptions")
    service = relationship("Service", back_populates="subscriptions")
    bookings = relationship("Booking", back_populates="subscription", cascade="all, delete-orphan")


class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id', ondelete='CASCADE'))
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'), nullable=False)
    trainer_schedule_id = Column(Integer, ForeignKey('trainer_schedules.id', ondelete='SET NULL'))

    booking_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(Enum(BookingStatus), default=BookingStatus.CONFIRMED)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("User", back_populates="bookings")
    subscription = relationship("Subscription", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    trainer_schedule = relationship("TrainerSchedule", back_populates="bookings")
    visits = relationship("Visit", back_populates="booking", cascade="all, delete-orphan")


class Visit(Base):
    __tablename__ = 'visits'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    trainer_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    training_session_id = Column(UUID(as_uuid=True), ForeignKey("training_sessions.id", ondelete="SET NULL"), nullable=True)
    booking_id = Column(UUID(as_uuid=True), ForeignKey('bookings.id', ondelete='CASCADE'))
    visit_type = Column(String(20), nullable=False)  # "gym", "training", "group_class"
    service_id = Column(Integer, ForeignKey('services.id', ondelete='CASCADE'))
    check_in_time = Column(DateTime, nullable=False)
    check_out_time = Column(DateTime)

    client = relationship("User", back_populates="visits", foreign_keys=[client_id])
    trainer = relationship("User", back_populates="trainer_visits", foreign_keys=[trainer_id])
    training_session = relationship("TrainingSession")
    booking = relationship("Booking", back_populates="visits")
    service = relationship("Service", back_populates="visits")


class Locker(Base):
    __tablename__ = 'lockers'
    id = Column(Integer, primary_key=True)
    locker_number = Column(String(20), unique=True, nullable=False)
    zone = Column(String(50))
    gender = Column(String(10))  # "men" or "women"
    status = Column(String(20), default="free")  # "free" or "occupied"
    code = Column(Integer)  # Код для открытия шкафчика
    is_available = Column(Boolean, default=True)
    occupied_by_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    occupied_at = Column(DateTime, nullable=True)


class Payment(Base):
    __tablename__ = 'payments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contract_id = Column(UUID(as_uuid=True), ForeignKey('contracts.id', ondelete='SET NULL'))
    yookassa_payment_id = Column(String, unique=True, index=True)

    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    client = relationship("User", back_populates="payments")
    contract = relationship("Contract", back_populates="payments")

