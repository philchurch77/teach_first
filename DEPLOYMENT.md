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

`DJANGO_SECRET_KEY` and `DJANGO_DEBUG` both **fail closed**. `DEBUG` defaults to
`False` when the variable is absent, and outside `DEBUG` a missing
`DJANGO_SECRET_KEY` raises `ImproperlyConfigured` at startup rather than
substituting a published development value. A deploy that forgets either one
will refuse to boot instead of coming up looking healthy.

## Local development

Because of the above, local work must opt in to debug mode:

- `DJANGO_DEBUG=1`

Set it in your shell or your editor's run configuration. With no
`DJANGO_SECRET_KEY` set and `DJANGO_DEBUG` unset, `manage.py` exits with
`ImproperlyConfigured`; if a key *is* present but `DJANGO_DEBUG` is not, the
test suite instead fails with `301 != 200`, because `SECURE_SSL_REDIRECT` is on
outside debug mode. Either way the fix is `DJANGO_DEBUG=1`, and neither is a
broken checkout. In debug mode a fresh random `SECRET_KEY` is generated per
process, so no key is required locally and none is committed.

**`DJANGO_DEBUG=1` is never the fix for a problem on the server.** It is the
one input that disables secure cookies, HSTS and the SSL redirect, publishes
tracebacks, and replaces the secret key with a throwaway — and the site comes
up looking perfectly healthy while it does. If the server reports a missing
secret key, set the secret key. Settings will refuse to start with debug on
when a hosting marker (`WEBSITE_HOSTNAME`, `DYNO`, `K_SERVICE`) is present, but
do not rely on that catching every platform.

## 2) Install dependencies

- `pip install -r requirements.txt`

## 3) Database

This project currently uses SQLite (`db.sqlite3`). For a hosted production environment, you’ll usually want Postgres instead (SQLite files can be lost on ephemeral filesystems).

If you keep SQLite, make sure the hosting platform persists the filesystem.

## 4) Run migrations

- `python manage.py migrate`

## 5) Collect static files — a missed step here takes the site down

WhiteNoise is configured for static files. Outside debug mode it uses a
**manifest**, and the page's stylesheet is resolved through it:

- `python manage.py collectstatic --clear --noinput`

Three things to know, because the failure modes are not obvious:

- **If the manifest is missing, every request is a 500**, not a degraded page.
  `{% static 'flow/flow.css' %}` raises `Missing staticfiles manifest entry`
  during template render, and it is the first static reference in the document.
- **`--clear` matters.** A `STATIC_ROOT` left over from a previous deploy can
  serve *old* CSS at 200 under a hashed, far-future-immutable URL. The new
  design silently never appears and nothing reports an error. A half-copied
  `STATIC_ROOT` is worse still: the page returns 200 and the stylesheet 404s, so
  the visitor gets unstyled text and no one is told.
- **Put this in the startup command or build pipeline, ahead of Gunicorn.**
  There is no Procfile, CI config or startup script in this repository, so
  today the step is a human remembering. If the platform runs it at build time,
  confirm `DJANGO_SECRET_KEY` is available *at build time* too — settings now
  refuse to import without it, where they previously fell back to a literal.

## 6) Start the server

Example (Gunicorn):

- `gunicorn teachflow.wsgi:application`

## 7) Schedule session cleanup — required

The flow keeps the visitor's answers in their session (see the data
classification section of `CLAUDE.md`). Sessions are database-backed and Django
**never deletes expired rows on its own**, so without this step `django_session`
accumulates those answers for the life of the deployment.

Run daily, via cron, an Azure WebJob, or the platform's scheduler:

- `python manage.py clearsessions`

Settings already limit each session to one hour of inactivity
(`SESSION_COOKIE_AGE`) and drop the cookie when the browser closes
(`SESSION_EXPIRE_AT_BROWSER_CLOSE`). This step is what makes the server side
match that promise.

## 8) Verify — check --deploy is necessary but not sufficient

- `python manage.py check --deploy`

That validates configuration. It renders no template, so **it passes with the
static manifest missing** and proves nothing about step 5. Also do:

- Fetch `/` and assert `200`.
- Pull the hashed stylesheet `href` out of that response and fetch it too.
  Assert `200`.
- Confirm `DJANGO_DEBUG` is not `1` in the running environment.

The stylesheet fetch is the only check that distinguishes "deployed" from
"deployed and unstyled, with nobody told".

## Note on HTTPS

`SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are always on outside debug
mode, so **this app requires HTTPS in production.** Setting
`DJANGO_SECURE_SSL_REDIRECT=0` on a host reachable over plain HTTP means the
browser refuses to store the session cookie: every answer starts a new session,
the visitor never gets past the first screen, and nothing reports an error.
Turning the redirect off is only safe when TLS terminates in front of the app
and `X-Forwarded-Proto` is set — which `SECURE_PROXY_SSL_HEADER` already
expects.
