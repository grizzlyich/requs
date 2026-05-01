# RequestTracker

Демонстрационный Django-проект для темы **«Разработка информационной системы учёта и контроля заявок в монтажном отделе предприятия»**.

Проект подготовлен в двух режимах:
- локальный запуск на SQLite;
- деплой на Vercel через Python Runtime + внешняя PostgreSQL-база.

## Что умеет система

- авторизация пользователей;
- регистрация новых пользователей с автоматическим назначением роли «Сотрудник»;
- роли пользователей через группы Django;
- создание и редактирование заявок;
- назначение исполнителя и проверяющего;
- изменение статуса заявки;
- комментарии и история изменений;
- фильтрация заявок по статусу, приоритету и просрочке;
- панель управления с краткой аналитикой;
- административная панель для управления пользователями и данными.

## Быстрый запуск локально

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

После запуска открой в браузере:

- основная система: `http://127.0.0.1:8000/`
- админ-панель: `http://127.0.0.1:8000/admin/`

## Демонстрационные аккаунты

| Роль | Логин | Пароль |
|---|---|---|
| Администратор | `admin_demo` | `admin12345` |
| Руководитель | `manager_demo` | `manager12345` |
| Сотрудник | `employee_demo` | `employee12345` |
| Контролёр | `controller_demo` | `controller12345` |

После `python manage.py seed_demo` пользователь `admin_demo` получает права персонала и суперпользователя для входа в Django Admin.

## Деплой на Vercel

### 1. Подготовь базу данных

Для Vercel нужна внешняя PostgreSQL-база. SQLite оставлен только для локального запуска.

Можно использовать:
- Neon;
- Supabase;
- Vercel Marketplace Postgres;
- любой внешний PostgreSQL-хостинг.

Нужна строка подключения вида:

```text
postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
```

### 2. Загрузи проект на GitHub

```bash
git init
git add .
git commit -m "Prepare RequestTracker for Vercel"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

### 3. Создай проект в Vercel

1. Открой Vercel.
2. Нажми **Add New → Project**.
3. Выбери репозиторий с проектом.
4. Framework Preset можно оставить как **Other** или автоопределение.
5. Перед деплоем добавь переменные окружения.

### 4. Переменные окружения для Vercel

Минимальный набор:

```text
DJANGO_SECRET_KEY=сгенерируй_длинный_секретный_ключ
DEBUG=False
ALLOWED_HOSTS=.vercel.app
CSRF_TRUSTED_ORIGINS=https://*.vercel.app
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DBNAME?sslmode=require
RUN_MIGRATIONS=1
SEED_DEMO=1
DJANGO_SUPERUSER_USERNAME=admin_demo
DJANGO_SUPERUSER_EMAIL=admin_demo@example.com
DJANGO_SUPERUSER_PASSWORD=admin12345
ALLOW_REGISTRATION=1
```

`RUN_MIGRATIONS=1` включает применение миграций во время сборки.  
`SEED_DEMO=1` создаёт демонстрационные роли, пользователей, подразделения и заявки.

После первого успешного деплоя можно убрать `SEED_DEMO` или поставить `SEED_DEMO=0`, чтобы демо-данные не пытались создаваться повторно.

### 5. Что было добавлено для Vercel

- `vercel.json` — настройки маршрутизации и Python Runtime;
- `wsgi.py` в корне проекта — точка входа для Vercel;
- `build_files.sh` — сборка static-файлов, миграции и демо-данные;
- `.python-version` — версия Python 3.12;
- `.env.example` — пример переменных окружения;
- `.vercelignore` — исключение локальной SQLite-базы и лишних файлов из деплоя;
- `WhiteNoise` — раздача static-файлов;
- `dj-database-url` и `psycopg` — подключение PostgreSQL через `DATABASE_URL`.

## Генерация секретного ключа Django

Локально можно выполнить:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Полученный ключ вставь в переменную `DJANGO_SECRET_KEY` в Vercel.

## Если админка не пускает

Можно создать или обновить суперпользователя командой:

```bash
python manage.py create_admin_from_env
```

Перед этим должны быть заданы:

```text
DJANGO_SUPERUSER_USERNAME
DJANGO_SUPERUSER_EMAIL
DJANGO_SUPERUSER_PASSWORD
```

Локально проще:

```bash
python manage.py createsuperuser
```

## Что показать на скриншотах для отчёта

1. Страница входа.
2. Главная панель с карточками статистики.
3. Список заявок с фильтрами.
4. Форма создания заявки.
5. Карточка заявки.
6. Блок истории изменения статуса.
7. Административная панель Django.

## Стек

- Python;
- Django;
- SQLite для локального режима;
- PostgreSQL для Vercel;
- WhiteNoise;
- Bootstrap 5.

## Структура проекта

- `request_tracker/` — настройки проекта;
- `tickets/` — приложение с моделями, формами, представлениями и тестами;
- `templates/` — HTML-шаблоны;
- `static/` — стили;
- `docs/` — вспомогательные материалы для отчёта.

## Исправление ошибки Vercel Function Runtimes

Если Vercel выдаёт ошибку:

```text
Error: Function Runtimes must have a valid version, for example `now-php@1.0.0`.
```

нужно удалить из `vercel.json` блок с явным указанием runtime `python3.12`.
Vercel сам определяет Python-приложение по `requirements.txt` и корневому `wsgi.py`, где экспортируется переменная `app`.
