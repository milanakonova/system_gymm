"""
API для абонементов по залам (упрощенно, без оплаты)
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from scr.db.database import get_db
from scr.db.models import User, UserRole, GymZone, ZonePass
from scr.core.dependencies import require_role
from scr.payment import api
from scr.core.config import settings

router = APIRouter(prefix="/api/passes", tags=["passes"])
ZONE_PRICES = {
        1: float(settings.PRICE_GYM),
        2: float(settings.PRICE_GROUP),
        3: float(settings.PRICE_POOL)}


def _ensure_client_passes(db: Session, client_id: UUID) -> List[ZonePass]:
    """Гарантируем что у клиента есть абонемент на каждый активный зал."""
    zones = db.query(GymZone).filter(GymZone.is_active == True).all()
    existing = db.query(ZonePass).filter(ZonePass.client_id == client_id).all()
    existing_by_zone = {p.gym_zone_id: p for p in existing}

    created_any = False
    for z in zones:
        if z.id not in existing_by_zone:
            p = ZonePass(client_id=client_id, gym_zone_id=z.id, remaining_visits=0)
            db.add(p)
            created_any = True

    if created_any:
        db.commit()

    return db.query(ZonePass).filter(ZonePass.client_id == client_id).all()


@router.get("/me")
async def get_my_passes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    passes = _ensure_client_passes(db, current_user.id)
    # Возвращаем ровно то, что нужно фронту
    result = []
    for p in passes:
        result.append({
            "id": str(p.id),
            "gym_zone_id": p.gym_zone_id,
            "zone_name": p.gym_zone.name if p.gym_zone else "",
            "remaining_visits": p.remaining_visits,
        })
    # Стабильный порядок (тренажерный, групповой, бассейн), если такие имена есть
    order = {"тренаж": 1, "групп": 2, "басс": 3}
    def key(x):
        n = (x["zone_name"] or "").lower()
        for k, v in order.items():
            if k in n:
                return v
        return 999
    result.sort(key=key)
    return result


@router.post("/me/{gym_zone_id}/topup", status_code=status.HTTP_200_OK)
async def topup_pass(
    gym_zone_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.CLIENT))
):
    zone = db.query(GymZone).filter(GymZone.id == gym_zone_id, GymZone.is_active == True).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Зал не найден")

    # Активируем оплату
    price = ZONE_PRICES.get(gym_zone_id)
    if not price:
        raise HTTPException(status_code=400, detail="Цена не настроена")

    payment_result = await api.create_payment(
        amount=price,
        gym_zone_id=gym_zone_id,
        current_user=current_user,
        db=db
    )

    # Возвращаем фронту ссылку на оплату
    return {
        "confirmation_url": payment_result["confirmation_url"],
        "status": "ok"
    }