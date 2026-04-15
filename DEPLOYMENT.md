# Deployment notes (Django)

This project is a simple Django app intended to be deployed behind a production WSGI server.

## 1) Set environment variables (production)

Required:

- `DJANGO_SECRET_KEY` = a long random string
- `DJANGO_DEBUG` = `0`
- `DJANGO_ALLOWED_HOSTS` = comma-separated hostnames (e.g. `example.com,www.example.com`)
- `DJANGO_CSRF_TRUSTED_ORIGINS` = comma-separated origins including scheme (e.g. `https://example.com,https://www.example.com`)

Optional (recommended behind HTTPS):

- `DJANGO_SECURE_SSL_REDIRECT` = `1`

See `.env.example` for a template.

## 2) Install dependencies

- `pip install -r requirements.txt`

## 3) Database

This project currently uses SQLite (`db.sqlite3`). For a hosted production environment, you’ll usually want Postgres instead (SQLite files can be lost on ephemeral filesystems).

If you keep SQLite, make sure the hosting platform persists the filesystem.

## 4) Run migrations

- `python manage.py migrate`

## 5) Collect static files

WhiteNoise is configured for static files.

- `python manage.py collectstatic --noinput`

## 6) Start the server

Example (Gunicorn):

- `gunicorn teachflow.wsgi:application`

## 7) Verify

- `python manage.py check --deploy`
