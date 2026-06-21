"""
Сервис для работы с входом/выходом из зала и шкафчиками
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from scr.db.models import User, UserRole, Visit, Subscription, SubscriptionType
from scr.db.repositories.user_repository import UserRepository
from scr.db.repositories.subscription_repository import SubscriptionRepository
from scr.services.locker_service import LockerService
from scr.services.contract_service import ContractService


class GymService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.subscription_repo = SubscriptionRepository(db)
        self.locker_service = LockerService(db)
        self.contract_service = ContractService(db)

    def enter_gym(self, current_user: User) -> dict:
        """Вход клиента в зал"""
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только клиенты могут входить в зал"
            )

        # Проверка, не находится ли клиент уже в зале
        if current_user.in_gym:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Клиент уже находится в зале"
            )

        # Получаем активные абонементы
        active_subscriptions = self.subscription_repo.get_active_subscriptions(current_user.id)
        
        if not active_subscriptions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет активных абонементов. Пожалуйста, оформите абонемент."
            )

        # Проверяем наличие доступных посещений
        has_available_visits = False
        subscription_to_use = None

        for subscription in active_subscriptions:
            if subscription.subscription_type == SubscriptionType.VISIT_BASED:
                if subscription.remaining_visits and subscription.remaining_visits > 0:
                    has_available_visits = True
                    subscription_to_use = subscription
                    break
            elif subscription.subscription_type == SubscriptionType.TIME_BASED:
                if not subscription.end_date or subscription.end_date >= datetime.now().date():
                    has_available_visits = True
                    subscription_to_use = subscription
                    break

        if not has_available_visits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нет доступных посещений в абонементах"
            )

        # Пытаемся назначить шкафчик
        locker = None
        locker_info = None
        if current_user.gender:
            locker = self.locker_service.assign_locker_to_user(
                current_user.id,
                current_user.gender
            )
            if locker:
                locker_info = {
                    "id": locker.id,
                    "code": locker.code,
                    "gender": locker.gender
                }

        if not locker:
            # Если нет шкафчиков, все равно разрешаем вход, но без шкафчика
            pass

        # Обновляем статус клиента
        current_user.in_gym = True
        if locker:
            current_user.current_locker_id = locker.id
        self.user_repo.update(current_user)

        # Создаем запись о посещении
        visit = Visit(
            client_id=current_user.id,
            visit_type="gym",
            check_in_time=datetime.now(timezone.utc)
        )
        if subscription_to_use:
            visit.service_id = subscription_to_use.service_id
        self.db.add(visit)
        self.db.commit()

        # Списываем посещение
        if subscription_to_use:
            self.contract_service.use_visit(subscription_to_use.id)

        return {
            "success": True,
            "message": f"Добро пожаловать, {current_user.first_name} {current_user.last_name}!",
            "locker_info": locker_info,
            "visit_id": str(visit.id)
        }

    def exit_gym(self, current_user: User) -> dict:
        """Выход клиента из зала"""
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только клиенты могут выходить из зала"
            )

        if not current_user.in_gym:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Клиент не находится в зале"
            )

        # Освобождаем шкафчик, если был занят
        if current_user.current_locker_id:
            self.locker_service.release_locker(current_user.current_locker_id)
            current_user.current_locker_id = None

        # Обновляем статус клиента
        current_user.in_gym = False
        self.user_repo.update(current_user)

        # Обновляем запись о посещении
        visit = self.db.query(Visit).filter(
            Visit.client_id == current_user.id,
            Visit.check_out_time.is_(None)
        ).order_by(Visit.check_in_time.desc()).first()

        if visit:
            visit.check_out_time = datetime.now(timezone.utc)
            self.db.commit()

        return {
            "success": True,
            "message": f"До свидания, {current_user.first_name} {current_user.last_name}!"
        }

    def get_gym_status(self, current_user: User) -> dict:
        """Получение статуса клиента в зале"""
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Только клиенты могут проверять статус"
            )

        locker_info = None
        if current_user.current_locker_id:
            locker = self.locker_service.get_user_locker(current_user.id)
            if locker:
                locker_info = {
                    "id": locker.id,
                    "code": locker.code,
                    "gender": locker.gender
                }

        # Получаем активные абонементы
        active_subscriptions = self.subscription_repo.get_active_subscriptions(current_user.id)
        visits_remaining = 0
        for sub in active_subscriptions:
            if sub.subscription_type == SubscriptionType.VISIT_BASED:
                if sub.remaining_visits:
                    visits_remaining += sub.remaining_visits

        return {
            "in_gym": current_user.in_gym,
            "locker_info": locker_info,
            "visits_remaining": visits_remaining,
            "active_subscriptions_count": len(active_subscriptions)
        }

