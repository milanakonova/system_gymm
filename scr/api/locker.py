from fastapi import HTTPException, APIRouter

from scr.module.lockerFunc import find_available_locker
from scr.db.struct import Client

router = APIRouter()


# Временное хранилище данных (в реальном приложении используйте БД)


@router.post("/locker/find")
async def find_locker(client: Client):

    if not client.in_gym:
        raise HTTPException(
            status_code=403,  # Forbidden
            detail="Клиент не находится в зале. Для получения шкафчика необходимо быть в зале."
        )

        # Проверяем, что у клиента еще нет шкафчика
    if client.locker_id is not None:
        raise HTTPException(
            status_code=409,  # Conflict
            detail=f"У клиента уже есть шкафчик (ID: {client.locker_id}). Нельзя занять второй шкафчик."
        )
    try:
        locker_code, locker_id = find_available_locker(client)
        if locker_code:
            return {
                "success": True,
                "message": "Найден подходящий шкафчик",
                "locker_id": locker_id,
                "locker_code": locker_code,
                "client_name": client.full_name,
                "client_gender": client.gender
            }
        else:
            return {
                "success": False,
                "message": "Свободных шкафчиков не найдено",
                "client_gender": client.gender
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

