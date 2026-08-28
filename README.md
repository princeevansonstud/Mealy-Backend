# Mealy Backend

Backend for **Mealy** — a food ordering platform connecting customers with caterers.

## Architecture

This project uses a hybrid setup:

- **Django** handles the web framework layer: URL routing, Django REST Framework (DRF) views/serializers, middleware, and the WSGI server.
- **SQLAlchemy** (with Alembic for migrations) is the actual ORM and data layer — **not** Django's built-in ORM.

Key implications:

- `INSTALLED_APPS` does **not** include `django.contrib.auth`, `django.contrib.contenttypes`, or `django.contrib.admin`. Django's own ORM-based auth is not in use.
- There is no `DATABASES` setting configured for Django — all database access goes through SQLAlchemy.
- A custom `config.db.SQLAlchemySessionMiddleware` bridges a SQLAlchemy session into each Django request, available in views as `request.db`.
- Authentication uses a custom DRF authentication class, `authentication.jwt.SQLAlchemyJWTAuthentication`, built around SQLAlchemy-based `User` records — not Django's auth system.
- All models (`authentication/models.py`, `meals/models.py`, etc.) are SQLAlchemy models (`Base`, `Mapped`, `mapped_column`) — **not** Django models (`models.Model`).

If you're used to standard Django projects, this is the main thing to unlearn: don't reach for `django.contrib.auth`, Django migrations, or the Django ORM here. Use SQLAlchemy sessions and Alembic instead.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python3 manage.py runserver
```

## Apps

- `authentication/` — user accounts, JWT-based login/register/logout/refresh
- `meals/` — meal options, daily menus, and daily menu items

## API Endpoints

### Auth (`/api/auth/`)
- `POST /register/`
- `POST /login/`
- `POST /token/refresh/`
- `POST /logout/`
- `GET /me/`

### Meals (`/api/meals/`)
- `GET /options/` — list all meal options
- `POST /options/` — create a meal option
- `POST /daily-menu/` — create a daily menu
- `GET /daily-menu/today/` — get today's menu with linked meal options
- `POST /daily-menu-items/` — link a meal option into a daily menu

## Notes

- `requirements.txt` still lists Django, DRF, and django-cors-headers even though Django's ORM isn't used — Django itself is a real dependency (the web framework layer), just not its ORM.
- `bcrypt` is pinned to `4.0.1` in `requirements.txt` due to a known incompatibility with `passlib==1.7.4` in newer bcrypt versions.
