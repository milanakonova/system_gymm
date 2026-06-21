# Система управления тренажерным залом

Проект "Система управления тренажерным залом" — веб-приложение для автоматизации ключевых бизнес-процессов современного фитнес-центра. Система обеспечивает эффективное управление пользователями, организацию расписания занятий, учет посещений и контроль доступа, что позволяет оптимизировать операционную деятельность зала, повысить качество обслуживания клиентов и снизить административные затраты.

**Основное**
- **Архитектура**: REST/HTTP API на FastAPI, PostgreSQL в качестве БД.
- **Точка входа**: [scr/main.py](scr/main.py#L1)
- **Docker**: [Dockerfile](Dockerfile#L1) и [docker-compose.yml](docker-compose.yml#L1)
- **Инициализация базы**: [init_database.py](init_database.py#L1) и [scr/db/init_db.py](scr/db/init_db.py#L1)
- **Конфигурация**: [scr/core/config.py](scr/core/config.py#L1) (читает переменные из `.env`)

**Особенности**
- Управление пользователями и ролями
- Планирование и расписание тренеров
- Система бронирования занятий и шкафчиков
- Учёт посещений и простая история тренировок
- Интеграция с платежной системой (Yooxassa/псевдо-ключи)

**Технологии**
- Python 3.11
- FastAPI + Uvicorn
- SQLAlchemy (ORM)
- PostgreSQL
- Docker / Docker Compose

**Требования**
- Docker Desktop (рекомендуется) или локально установленный PostgreSQL
- Python 3.11 (если запуск локально)

**Файлы проекта**
- [Dockerfile](Dockerfile#L1) — образ для сервиса API.
- [docker-compose.yml](docker-compose.yml#L1) — разворачивает сервисы `api` и `db` (Postgres).
- [requirements.txt](requirements.txt#L1) — зависимости при локальном запуске.
- [scr/core/config.py](scr/core/config.py#L1) — переменные окружения и конфигурация приложения.

**Быстрый старт — Docker (рекомендуемый)**
1. Создайте файл `.env` в корне проекта. Минимальный пример:

```env
DB_USERNAME=postgres
DB_PASSWORD=1234
DB_DATABASE=gym_sistem
DATABASE_URL=postgresql://postgres:1234@db:5432/gym_sistem
SECRET_KEY=change_me
CONFIGURATION_SHOP_KEY=shop_key
CONFIGURATION_SECRET_KEY=shop_secret
PAYMENT_RETURN_URL=http://localhost:8000/payment/return
PRICE_GYM=500
PRICE_GROUP=800
PRICE_POOL=700
```

2. Сборка и запуск сервисов:

```bash
docker compose up --build -d
```

3. Просмотр логов API (опционально):

```bash
docker compose logs -f api
```

4. Открыть документацию API в браузере:

- http://localhost:8000/api/docs

Примечания:
- Внутри контейнера `api` хост базы должен быть `db` (как в `DATABASE_URL` выше).
- `docker-compose.yml` пробрасывает порт Postgres `5432` наружу, поэтому можно подключиться к БД извне.

**Локальный запуск (без Docker)**
1. Создайте виртуальное окружение и установите зависимости:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Подготовьте `.env` (пример выше), где `DATABASE_URL` указывает на ваш локальный Postgres, например:

```env
DATABASE_URL=postgresql://postgres:1234@localhost:5432/gym_sistem
```

3. Инициализация базы данных (создаст таблицы и сиды):

```bash
python init_database.py
```

4. Запуск сервера:

```bash
uvicorn scr.main:app --host 0.0.0.0 --port 8000 --reload
# или
python scr/main.py
```

5. Откройте: http://localhost:8000/api/docs

**Переменные окружения (ключевые)**
- `DATABASE_URL` — строка подключения к PostgreSQL.
- `DB_USERNAME`, `DB_PASSWORD`, `DB_DATABASE` — используются в `docker-compose.yml`.
- `SECRET_KEY` — секрет для JWT.
- `CONFIGURATION_SHOP_KEY`, `CONFIGURATION_SECRET_KEY`, `PAYMENT_RETURN_URL` — данные для платежного сервиса (можно временно заглушить).
- `PRICE_GYM`, `PRICE_GROUP`, `PRICE_POOL` — базовые цены.

Конфигурация загружается из [scr/core/config.py](scr/core/config.py#L1).

**Инициализация и миграции**
- При старте приложение выполняет простую авто-миграцию (добавляет недостающие колонки) и вызывает `Base.metadata.create_all` для создания таблиц при отсутствии.
- Для явной инициализации/сидирования используйте `python init_database.py`.

**Отладка / распространённые проблемы**
- Проблемы с подключением к БД: проверьте, что Postgres запущен и `DATABASE_URL` правильный.
- В Docker: внутри контейнера API хост БД — `db`, не `localhost`.
- Отказ в правах при создании БД: убедитесь, что пользователь имеет право `CREATEDB`.
- Отсутствующие переменные в `.env` могут привести к ошибкам при старте.

**Где посмотреть код**
- Точка входа приложения: [scr/main.py](scr/main.py#L1)
- Скрипт инициализации БД: [init_database.py](init_database.py#L1)
- Логика работы с БД: [scr/db/init_db.py](scr/db/init_db.py#L1) и [scr/db/models.py](scr/db/models.py#L1)
- Конфигурация: [scr/core/config.py](scr/core/config.py#L1)
