# API организационной структуры

REST API для управления организационной структурой компании: иерархия подразделений (дерево) и сотрудники внутри подразделений.

Реализация тестового задания: FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker Compose.

![Корневой эндпоинт API](screen.png)

---

## Содержание

- [Быстрый старт](#быстрый-старт)
- [Стек технологий](#стек-технологий)
- [Структура проекта](#структура-проекта)
- [Модели данных](#модели-данных)
- [Эндпоинты API](#эндпоинты-api)
- [Бизнес-правила](#бизнес-правила)
- [Примеры запросов](#примеры-запросов)
- [Переменные окружения](#переменные-окружения)
- [Локальная разработка без Docker](#локальная-разработка-без-docker)
- [Тесты](#тесты)
- [Устранение неполадок](#устранение-неполадок)

---

## Быстрый старт

### Требования

- Docker и Docker Compose
- (опционально) Python 3.12+ — для локального запуска и тестов

### Запуск

```bash
cd hitalent
docker compose up --build
```

При старте контейнера `api` автоматически выполняются миграции (`alembic upgrade head`), затем запускается сервер.

### Полезные URL

| URL | Описание |
|-----|----------|
| http://localhost:8000/ | Краткое описание API и список эндпоинтов |
| http://localhost:8000/docs | Swagger UI — интерактивная документация |
| http://localhost:8000/redoc | ReDoc — альтернативная документация |
| http://localhost:8000/health | Проверка работоспособности |

Проверка:

```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

Остановка:

```bash
docker compose down
```

Удаление данных БД (volume):

```bash
docker compose down -v
```

---

## Стек технологий

| Компонент | Назначение |
|-----------|------------|
| **FastAPI** | HTTP API, валидация, OpenAPI |
| **Pydantic** | Схемы запросов и ответов |
| **SQLAlchemy 2** | ORM, работа с PostgreSQL |
| **Alembic** | Миграции схемы БД |
| **PostgreSQL 16** | Хранение данных |
| **Docker Compose** | Локальный запуск приложения и БД |
| **pytest + httpx** | Автотесты |
| **uvicorn** | ASGI-сервер |

---

## Структура проекта

```
hitalent/
├── app/
│   ├── main.py                 # Точка входа FastAPI, обработчики ошибок, /, /health
│   ├── config.py               # Настройки из переменных окружения
│   ├── database.py             # Подключение к БД, сессии
│   ├── exceptions.py           # Исключения приложения (404, 409, 400)
│   ├── logging_config.py       # Настройка логирования
│   ├── models/                 # SQLAlchemy-модели (Department, Employee)
│   ├── schemas/                # Pydantic-схемы (валидация, trim полей)
│   ├── services/               # Бизнес-логика (DepartmentService)
│   └── api/
│       ├── deps.py             # Зависимости FastAPI (сессия, сервис)
│       └── routes/
│           └── departments.py  # HTTP-эндпоинты
├── alembic/                    # Миграции Alembic
│   └── versions/
├── tests/                      # Pytest-тесты
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh               # Миграции + запуск uvicorn
├── requirements.txt
└── README.md
```

Архитектура: **маршруты → сервис → ORM**. HTTP-слой не содержит бизнес-логики; валидация входных данных — в Pydantic-схемах.

---

## Модели данных

### Department (подразделение)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | Первичный ключ |
| `name` | str | Название (1–200 символов, не пустое) |
| `parent_id` | int \| null | Родительское подразделение (дерево) |
| `created_at` | datetime | Дата создания |

### Employee (сотрудник)

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | int | Первичный ключ |
| `department_id` | int | Подразделение (FK) |
| `full_name` | str | ФИО (1–200 символов) |
| `position` | str | Должность (1–200 символов) |
| `hired_at` | date \| null | Дата приёма (опционально) |
| `created_at` | datetime | Дата создания |

### Связи

- Подразделение **1 → N** сотрудников
- Подразделение **1 → N** дочерних подразделений (самоссылка через `parent_id`)
- Имя подразделения **уникально** в рамках одного родителя (`UNIQUE(parent_id, name)`)

---

## Эндпоинты API

### `GET /`

Краткая информация об API и ссылки на документацию.

### `GET /health`

Проверка, что сервис запущен.

---

### `POST /departments/` — создать подразделение

**Тело запроса:**

```json
{
  "name": "Backend",
  "parent_id": 1
}
```

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `name` | да | Название подразделения |
| `parent_id` | нет | ID родителя; `null` — корневое подразделение |

**Ответ:** `201 Created` — созданное подразделение.

**Ошибки:**

- `404` — родитель с указанным `parent_id` не найден
- `409` — подразделение с таким именем уже есть у этого родителя

---

### `POST /departments/{id}/employees/` — создать сотрудника

**Тело запроса:**

```json
{
  "full_name": "Иван Иванов",
  "position": "Разработчик",
  "hired_at": "2024-03-15"
}
```

| Поле | Обязательно | Описание |
|------|-------------|----------|
| `full_name` | да | ФИО |
| `position` | да | Должность |
| `hired_at` | нет | Дата приёма (`YYYY-MM-DD`) |

**Ответ:** `201 Created` — созданный сотрудник.

**Ошибки:**

- `404` — подразделение с `{id}` не существует

---

### `GET /departments/{id}` — подразделение с деревом и сотрудниками

**Query-параметры:**

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `depth` | `1` | Сколько **уровней дочерних** подразделений вернуть в `children` (1–5). `depth=1` — только прямые дочерние, `depth=2` — дочерние и внуки и т.д. |
| `include_employees` | `true` | Включать список сотрудников (`false` — пустые массивы `employees`) |

**Пример ответа:**

```json
{
  "department": {
    "id": 1,
    "name": "Компания",
    "parent_id": null,
    "created_at": "2026-05-27T12:00:00Z"
  },
  "employees": [],
  "children": [
    {
      "id": 2,
      "name": "Разработка",
      "parent_id": 1,
      "created_at": "...",
      "employees": [
        {
          "id": 1,
          "department_id": 2,
          "full_name": "Алиса",
          "position": "Dev",
          "hired_at": null,
          "created_at": "..."
        }
      ],
      "children": []
    }
  ]
}
```

Сотрудники сортируются по `full_name`. Дочерние подразделения — по `name`.

**Семантика `depth`:** параметр задаёт глубину вложенности **ниже** запрашиваемого подразделения, не включая его само. Например, при `depth=1` в `children` будут только подразделения с `parent_id = {id}`; вложенности глубже не раскрываются.

**Ошибки:**

- `404` — подразделение не найдено

---

### `PATCH /departments/{id}` — обновить подразделение

**Тело запроса** (оба поля опциональны):

```json
{
  "name": "Новое название",
  "parent_id": 3
}
```

Можно передать только `name`, только `parent_id` или оба поля. `parent_id: null` — сделать корневым.

**Ошибки:**

- `404` — подразделение или новый родитель не найдены
- `409` — цикл в дереве (нельзя переместить в своё поддерево) или дубликат имени у родителя

---

### `DELETE /departments/{id}` — удалить подразделение

**Query-параметры:**

| Параметр | Обязательно | Описание |
|----------|-------------|----------|
| `mode` | да | `cascade` или `reassign` |
| `reassign_to_department_id` | при `mode=reassign` | ID подразделения для перевода сотрудников |

#### Режим `cascade`

Удаляет подразделение, **всех сотрудников** и **все дочерние подразделения** рекурсивно. Каскад настроен на уровне БД (`ON DELETE CASCADE`).

```bash
curl -X DELETE "http://localhost:8000/departments/2?mode=cascade"
```

**Ответ:** `204 No Content`

#### Режим `reassign`

- Сотрудников переводит в `reassign_to_department_id`
- Дочерние подразделения перепривязывает к родителю удаляемого (на уровень выше) — в ТЗ это не описано явно, но иначе удаление нарушит целостность дерева
- Само подразделение удаляется

```bash
curl -X DELETE "http://localhost:8000/departments/2?mode=reassign&reassign_to_department_id=1"
```

**Ошибки:**

- `400` — не указан `reassign_to_department_id` при `mode=reassign`
- `404` — подразделение или целевое для reassign не найдены

---

## Бизнес-правила

| Правило | Код ответа |
|---------|------------|
| Нельзя создать сотрудника в несуществующем подразделении | `404` |
| `name`, `full_name`, `position` — не пустые, длина 1–200, пробелы по краям обрезаются | `422` |
| Имя подразделения уникально в рамках одного `parent_id` | `409` |
| Нельзя сделать подразделение родителем самого себя | `409` |
| Нельзя создать цикл при смене `parent_id` | `409` |
| `depth` при GET — от 1 до 5 | `422` |

---

## Примеры запросов

Полный сценарий после чистого запуска:

```bash
# 1. Корневое подразделение
curl -s -X POST http://localhost:8000/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Компания"}'

# 2. Дочернее подразделение (parent_id = 1)
curl -s -X POST http://localhost:8000/departments/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Разработка", "parent_id": 1}'

# 3. Сотрудник в подразделении 2
curl -s -X POST http://localhost:8000/departments/2/employees/ \
  -H "Content-Type: application/json" \
  -d '{"full_name": "Алиса Петрова", "position": "Backend-разработчик", "hired_at": "2024-01-10"}'

# 4. Дерево на 3 уровня вглубь
curl -s "http://localhost:8000/departments/1?depth=3&include_employees=true"

# 5. Переименование
curl -s -X PATCH http://localhost:8000/departments/2 \
  -H "Content-Type: application/json" \
  -d '{"name": "Отдел разработки"}'

# 6. Удаление с переводом сотрудников
curl -s -X DELETE "http://localhost:8000/departments/2?mode=reassign&reassign_to_department_id=1"
```

Удобнее тестировать через **Swagger**: http://localhost:8000/docs

---

## Переменные окружения

Скопируйте пример:

```bash
cp .env.example .env
```

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `DATABASE_URL` | `postgresql://postgres:postgres@db:5432/hitalent` (в Docker) | Строка подключения PostgreSQL |
| `LOG_LEVEL` | `INFO` | Уровень логирования (`DEBUG`, `INFO`, …) |

В `docker-compose.yml` для сервиса `api` уже заданы нужные значения.

---

## Локальная разработка без Docker

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Поднимите PostgreSQL (например, только БД из Compose):

```bash
docker compose up db -d
```

Примените миграции и запустите сервер:

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hitalent
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Создание новой миграции после изменения моделей:

```bash
alembic revision --autogenerate -m "описание изменений"
alembic upgrade head
```

---

## Тесты

По умолчанию тесты используют **SQLite в памяти** — дополнительная БД не нужна:

```bash
pip install -r requirements.txt
pytest -v
```

Запуск против PostgreSQL:

```bash
docker compose up db -d
docker compose exec db psql -U postgres -c "CREATE DATABASE hitalent_test;"
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hitalent_test
pytest -v
```

Покрытие сценариев:

- создание подразделения и сотрудника;
- получение дерева с `depth`;
- уникальность имени у одного родителя;
- запрет циклов в дереве;
- каскадное удаление;
- удаление с переводом сотрудников (`reassign`);
- 404 при создании сотрудника в несуществующем подразделении;
- `depth` (1 — прямые дети, 2 — внуки), `include_employees=false`;
- trim пробелов, PATCH по отдельным полям, ошибки reassign/mode.

---

## Устранение неполадок

### `{"detail":"Not Found"}` на `/`

Раньше корневой путь не был определён. Сейчас `GET /` возвращает описание API. Если видите 404 — пересоберите контейнер:

```bash
docker compose up --build -d
```

### `{"detail":"Подразделение не найдено"}`

Подразделение с таким `id` отсутствует в БД (удалено или ещё не создано). Проверьте id или создайте подразделение заново.

### `permission denied` при работе с Docker

Добавьте пользователя в группу `docker` и перелогиньтесь:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Порт 8000 занят

Измените проброс порта в `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"
```

### Сброс данных БД

```bash
docker compose down -v
docker compose up --build
```

---

## Лицензия

Учебный / тестовый проект.
