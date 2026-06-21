from yookassa import Configuration, Payment
import uuid
from scr.core.config import settings

Configuration.account_id = settings.CONFIGURATION_SHOP_KEY
Configuration.secret_key = settings.CONFIGURATION_SECRET_KEY

class YooKassaService:
    # Создаёт платёж в Yookassa и возвращает данные для редиректа
    @staticmethod
    def create_payment(amount: float, description: str, client_id: str, gym_zone_id: int) -> dict:
        payment_data ={
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.PAYMENT_RETURN_URL
            },
            "capture": True,
            "description": description,
            "metadata": {
                "client_id": client_id,
                "gym_zone_id": str(gym_zone_id)
            }
        }

        idempotence_key = str(uuid.uuid4())
        try:
            payment = Payment.create(payment_data, idempotence_key)
        except Exception as e:
            raise RuntimeError(f"YooKassa error: {e}")

        return {
            "payment_id": payment.id,
            "status": payment.status,
            "confirmation_url": payment.confirmation.confirmation_url
        }

    @staticmethod
    def get_payment_status(payment_id: str) -> dict:
        payment = Payment.find_one(payment_id)

        return {
            "payment_id": payment.id,
            "status": payment.status,
            "paid": payment.paid,
            "amount": payment.amount.value,
            "currency": payment.amount.currency,
            "description": payment.description
        }