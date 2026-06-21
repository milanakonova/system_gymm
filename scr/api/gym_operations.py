import random
from fastapi import HTTPException, APIRouter
from scr.db.clientDb import update_client_in_db
from scr.db.lockerDb import get_all_lockers_from_db, update_locker_in_db, reset_locker_in_db
from scr.db.struct import Client, LockerPydantic

router = APIRouter()


@router.post("/gym_operations/enter")
async def client_enter_gym(client: Client):
    try:
        # Проверяем, не находится ли клиент уже в зале
        if client.in_gym:
            return {
                "success": False,
                "message": "Клиент уже находится в зале.",
                "visits_remaining": client.visits_remaining,
                "client_name": client.full_name
            }

        # ШАГ 1: Проверяем наличие свободного шкафчика для клиента
        # Определяем пол клиента для выбора правильной раздевалки
        gender = "men" if client.gender == "male" else "women"

        # Получаем все шкафчики
        all_lockers = get_all_lockers_from_db()

        # Ищем свободный шкафчик подходящего пола
        free_locker = None
        for locker in all_lockers:
            if locker.gender == gender and locker.status == "free":
                free_locker = locker
                break

        # Если нет свободных шкафчиков - сразу возвращаем ошибку
        if free_locker is None:
            return {
                "success": False,
                "message": f"Нет свободных шкафчиков в {gender} раздевалке. Попробуйте позже.",
                "visits_remaining": client.visits_remaining,
                "client_name": client.full_name
            }

        # ШАГ 2: Бронируем шкафчик (назначаем его клиенту)
        new_code = random.randint(1000, 9999)

        # Обновляем шкафчик в БД - помечаем как занятый
        updated_locker = LockerPydantic(
            id=free_locker.id,
            gender=free_locker.gender,
            status="occupied",
            code=new_code
        )

        # Сохраняем изменения в БД
        saved_locker = update_locker_in_db(updated_locker)

        if saved_locker is None:
            return {
                "success": False,
                "message": "Ошибка при бронировании шкафчика.",
                "visits_remaining": client.visits_remaining,
                "client_name": client.full_name
            }

        # ШАГ 3: Проверяем, есть ли у клиента посещения
        if client.visits_remaining <= 0:
            # Если нет посещений - ОСВОБОЖДАЕМ шкафчик обратно
            reset_locker_in_db(free_locker.id)
            return {
                "success": False,
                "message": "Посещения закончились. Пожалуйста, пополните абонемент. Шкафчик освобожден.",
                "visits_remaining": client.visits_remaining,
                "client_name": client.full_name
            }

        # ШАГ 4: Обновляем статус клиента и списываем посещение
        client.in_gym = True
        client.visits_remaining -= 1
        client.locker_id = saved_locker.id  # Сохраняем ID шкафчика у клиента

        # Обновляем клиента в БД
        update_client_in_db(client)

        return {
            "success": True,
            "message": f"Добро пожаловать, {client.full_name}! Шкафчик #{saved_locker.id} забронирован. Код: {saved_locker.code}",
            "visits_remaining": client.visits_remaining,
            "client_name": client.full_name,
            "locker_info": {
                "id": saved_locker.id,
                "code": saved_locker.code,
                "gender": saved_locker.gender
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при входе в зал: {str(e)}"
        )


@router.post("/gym_operations/exit")
def client_exit_gym(client: Client):
    try:
        # Проверяем, находится ли клиент в зале
        if not client.in_gym:
            return {
                "success": False,
                "message": "Клиент не находится в зале.",
                "client_name": client.full_name
            }

        # Если у клиента был занят шкафчик - освобождаем его
        if client.locker_id is not None:
            # Освобождаем шкафчик в БД
            reset_locker_in_db(client.locker_id)

            # Сбрасываем ID шкафчика у клиента
            client.locker_id = None

        # Обновляем статус клиента
        client.in_gym = False

        # Обновляем данные клиента (в реальной БД)
        update_client_in_db(client)

        message = f"До свидания, {client.full_name}!"

        return {
            "success": True,
            "message": message,
            "client_name": client.full_name,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выходе из зала: {str(e)}"
        )

