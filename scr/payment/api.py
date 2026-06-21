from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from scr.payment.yookassa_service import YooKassaService
from scr.core.dependencies import get_current_active_user
from scr.db.database import get_db
from scr.db.models import User, Payment, PaymentStatus, ZonePass

router = APIRouter(prefix="/api/payments", tags=["payments"])

# Создание платежа и получение ссылки на оплату
async def create_payment(amount: float, gym_zone_id: int,
                         current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        payment = Payment(client_id=current_user.id, amount=amount, status=PaymentStatus.PENDING)
        db.add(payment)
        db.commit()
        db.refresh(payment)

        result = YooKassaService.create_payment(
            amount=amount,
            description="Пополнение абонемента",
            client_id=str(current_user.id),
            gym_zone_id=gym_zone_id
        )

        payment.yookassa_payment_id = result["payment_id"]
        db.commit()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Вебхук для получения информации о пройденной оплате
@router.post("/webhook")
async def yookassa_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()

        event = payload.get("event")
        payment_data = payload.get("object", {})
        payment_id = payment_data.get("id")
        status = payment_data.get("status")
        metadata = payment_data.get("metadata", {})

        if not payment_id:
            return {"status": "ignored"}

        payment = db.query(Payment).filter(Payment.yookassa_payment_id == payment_id).first()
        if not payment:
            return {"status": "ignored"}

        if event == "payment.succeeded":
            if payment.status != PaymentStatus.PAID:
                payment.status = PaymentStatus.PAID
                payment.paid_at = datetime.now(timezone.utc)

                client_id = metadata.get("client_id")
                gym_zone_id = metadata.get("gym_zone_id")

                zone_pass = db.query(ZonePass).filter(ZonePass.client_id == client_id,
                                                      ZonePass.gym_zone_id == gym_zone_id).first()

                if not zone_pass:
                    zone_pass = ZonePass(client_id=client_id, gym_zone_id=gym_zone_id, remaining_visits=0)
                db.add(zone_pass)
                db.flush()

            zone_pass.remaining_visits += 5
            db.commit()

        return {"status": "ok"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))