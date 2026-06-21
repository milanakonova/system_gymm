import random
from typing import Optional, Tuple

from scr.db.lockerDb import get_all_lockers_from_db, update_locker_in_db
from scr.db.struct import Client, LockerPydantic


def find_available_locker(client: Client) -> Optional[Tuple[int, int]]:
    """
    Находит доступный шкафчик для клиента
    Возвращает кортеж (locker_code, locker_id) или None
    """
    # Определяем пол для раздевалки
    gender = "men" if client.gender == "male" else "women"
    
    for locker in get_all_lockers_from_db():
        if locker.status == "free" and locker.gender == gender:
            # Генерируем новый код
            new_code = random.randint(1000, 9999)
            
            # Обновляем шкафчик
            updated_locker = LockerPydantic(
                id=locker.id,
                gender=locker.gender,
                status="occupied",
                code=new_code
            )
            saved_locker = update_locker_in_db(updated_locker)
            if saved_locker:
                return saved_locker.code, saved_locker.id
    return None

