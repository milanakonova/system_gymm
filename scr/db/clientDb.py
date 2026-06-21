from scr.db.struct import Client


def update_client_in_db(updated_client: Client) -> Client:
    """
    Обновляет данные клиента в БД
    В реальной системе здесь был бы UPDATE запрос к базе данных
    
    :param updated_client: Объект Client с обновленными данными
    :return: Обновленный объект Client
    """
    # Ищем клиента по ID в бд
    # Обновляем клиента в "БД"
    # В реальной БД здесь был бы UPDATE запрос
    client_id = updated_client.id or updated_client.client_id
    print(f"Имитация UPDATE запроса: клиент ID {client_id} обновлен")
    print(f"  - in_gym: {updated_client.in_gym}")
    print(f"  - visits_remaining: {updated_client.visits_remaining}")
    print(f"  - locker_id: {updated_client.locker_id}")
    return updated_client

