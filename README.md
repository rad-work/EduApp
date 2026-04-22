# EduAppMai

Базовый каркас платформы задач по программированию (аналог Codeforces/LeetCode) на стеке FastAPI + PostgreSQL + Redis.

## Tech stack
- Python 3.12
- FastAPI + Uvicorn
- PostgreSQL
- Redis
- SQLAlchemy + Alembic
- Jinja2 (HTML templates)
- Docker / Docker Compose

## Project structure
- `app/` - backend приложение FastAPI
- `templates/` - HTML шаблоны
- `static/` - CSS/JS/статические ассеты
- `alembic/` - миграции БД

## Quick start
1. Скопировать переменные окружения:
   - `cp .env.example .env`
2. Запустить сервисы:
   - `docker compose up --build`
3. Открыть API:
   - [http://localhost:8000/docs](http://localhost:8000/docs)
