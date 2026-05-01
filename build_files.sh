#!/bin/bash
set -e

echo "Installing Python dependencies..."
python -m pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Миграции лучше запускать только когда указана внешняя БД.
# На Vercel добавь переменную RUN_MIGRATIONS=1 для первого деплоя или когда меняются модели.
if [ "$RUN_MIGRATIONS" = "1" ]; then
  echo "Applying database migrations..."
  python manage.py migrate --noinput
else
  echo "Skipping migrations. Set RUN_MIGRATIONS=1 to enable them during build."
fi

# Для демонстрационного стенда можно сразу создать пользователей и тестовые заявки.
# Включай только для учебного/демо-проекта.
if [ "$SEED_DEMO" = "1" ]; then
  echo "Creating demo data..."
  python manage.py seed_demo
else
  echo "Skipping demo data. Set SEED_DEMO=1 to create it."
fi

# Создание админа из переменных окружения.
# DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Creating/updating superuser from env..."
  python manage.py create_admin_from_env
fi
