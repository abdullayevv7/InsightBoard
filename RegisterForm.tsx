version: "3.9"

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-insightboard}
      POSTGRES_USER: ${POSTGRES_USER:-insightboard}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-insightboard_secret}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-insightboard}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate --noinput &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4 --threads 2 --timeout 120"
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.${DJANGO_ENV:-development}
      - DATABASE_URL=postgres://${POSTGRES_USER:-insightboard}:${POSTGRES_PASSWORD:-insightboard_secret}@db:5432/${POSTGRES_DB:-insightboard}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
      - DEBUG=${DEBUG:-False}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS:-*}
      - CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS:-http://localhost,http://localhost:3000}
      - EMAIL_HOST=${EMAIL_HOST:-smtp.gmail.com}
      - EMAIL_PORT=${EMAIL_PORT:-587}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER:-}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD:-}
      - DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL:-noreply@insightboard.io}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A config worker -l info --concurrency=4
    volumes:
      - ./backend:/app
      - media_volume:/app/media
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.${DJANGO_ENV:-development}
      - DATABASE_URL=postgres://${POSTGRES_USER:-insightboard}:${POSTGRES_PASSWORD:-insightboard_secret}@db:5432/${POSTGRES_DB:-insightboard}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    volumes:
      - ./backend:/app
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.${DJANGO_ENV:-development}
      - DATABASE_URL=postgres://${POSTGRES_USER:-insightboard}:${POSTGRES_PASSWORD:-insightboard_secret}@db:5432/${POSTGRES_DB:-insightboard}
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY:-change-me-in-production}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    volumes:
      - frontend_build:/app/build
    environment:
      - REACT_APP_API_URL=${REACT_APP_API_URL:-/api}
    depends_on:
      - backend

  nginx:
    image: nginx:1.25-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/var/www/static
      - media_volume:/var/www/media
      - frontend_build:/var/www/frontend
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
  frontend_build:
