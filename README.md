# EduApp

Базовый каркас платформы для решения задач по программированию

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

## Языки посылок
Поддерживаются **Python**, **C** (GCC, стандарт C17), **C++** (G++, C++20), **Java** (OpenJDK / `javac`). Имена файлов и точные версии toolchain совпадают с образом проверки (`runner/Dockerfile`); кратко они показаны в выпадающем списке при отправке решения. Ввод — stdin, вывод — stdout.

После изменений в каталоге `runner/` пересоберите образ проверяющей среды (например `docker compose build` или пересборка тега `runner`), иначе контейнер может остаться со старым `execute.py`.

## Quick start
1. Скопировать переменные окружения:
   - `cp .env.example .env`
2. Запустить сервисы:
   - `docker compose up --build`
3. Открыть API:
   - [http://localhost:8000/docs](http://localhost:8000/docs)
