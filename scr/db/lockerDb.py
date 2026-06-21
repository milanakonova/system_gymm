import random
from typing import List

from scr.db.struct import LockerPydantic


def get_all_lockers_from_db() -> List[LockerPydantic]:
    """
    Получить все шкафчики из БД
    В реальной системе здесь был бы SELECT запрос
    """
    # Имитация данных из БД
    lockers = [
        LockerPydantic(id=1, gender="men", status="free", code=1234),
        LockerPydantic(id=2, gender="men", status="free", code=5678),
        LockerPydantic(id=3, gender="men", status="occupied", code=9012),
        LockerPydantic(id=4, gender="women", status="free", code=3456),
        LockerPydantic(id=5, gender="women", status="occupied", code=7890),
        LockerPydantic(id=6, gender="men", status="free", code=2345),
        LockerPydantic(id=7, gender="women", status="free", code=6789),
        LockerPydantic(id=8, gender="men", status="occupied", code=1122),
        LockerPydantic(id=9, gender="women", status="free", code=3344),
        LockerPydantic(id=10, gender="women", status="occupied", code=5566)
    ]
    return lockers


def update_locker_in_db(updated_locker: LockerPydantic) -> LockerPydantic:
    """
    Обновить шкафчик в БД
    В реальной системе здесь был бы UPDATE запрос

    Возвращает обновленный шкафчик или None если не найден
    """
    # 1. Получаем все шкафчики
    all_lockers = get_all_lockers_from_db()

    # 2. Ищем нужный шкафчик по ID
    for i, locker in enumerate(all_lockers):
        if locker.id == updated_locker.id:
            # 3. Обновляем данные шкафчика
            all_lockers[i] = updated_locker

            # Имитация сохранения в БД
            print(f"Имитация UPDATE запроса: шкафчик ID {updated_locker.id} обновлен")
            print(f"Новый статус: {updated_locker.status}, код: {updated_locker.code}")

            return updated_locker

    # Шкафчик не найден
    print(f"Шкафчик с ID {updated_locker.id} не найден")
    return None


def reset_locker_in_db(locker_id: int) -> LockerPydantic:
    """
    Сбросить шкафчик в БД - освободить и сгенерировать новый код

    Шаги:
    1. Проверяем существование шкафчика
    2. Если занят - освобождаем и генерируем новый код
    3. Если свободен - просто обновляем код
    4. Сохраняем изменения

    Возвращает обновленный шкафчик
    """
    # 1. Получаем все шкафчики
    all_lockers = get_all_lockers_from_db()

    # 2. Ищем нужный шкафчик
    for i, locker in enumerate(all_lockers):
        if locker.id == locker_id:
            # 3. Генерируем новый код
            new_code = random.randint(1000, 9999)

            # 4. Обновляем шкафчик
            updated_locker = LockerPydantic(
                id=locker.id,
                gender=locker.gender,
                status="free",  # Всегда освобождаем
                code=new_code
            )

            # 5. Сохраняем изменения
            all_lockers[i] = updated_locker

            # Имитация сохранения в БД
            print(f"Имитация UPDATE запроса: шкафчик ID {locker_id} сброшен")
            print(f"Новый статус: свободен, новый код: {new_code}")

            return updated_locker

    # Шкафчик не найден
    print(f"Шкафчик с ID {locker_id} не найден")
    return None

