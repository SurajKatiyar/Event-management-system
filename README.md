# Event Management System

This project supports two modes while keeping the same codebase and structure:

- Basic mode: current simple flow for learning and demos.
- Pro mode: optional security and production hardening through a separate layer.

## Project Modes

### Basic mode

- Keeps current behavior.
- Uses console email backend.
- Best for local development and simple project ZIP sharing.

### Pro mode

- Enables hardened settings from `event_register/pro_layer/security.py`.
- Adds HTTPS/security header/cookie/HSTS defaults.
- Supports SMTP and stronger production defaults.
- Activated only when `DJANGO_PRO_MODE=True`.

## Environment Variables

Use the sample env files under `deployment/env/`:

- `deployment/env/.env.basic.example`
- `deployment/env/.env.pro.example`

Main variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `SITE_BASE_URL`
- `DJANGO_EMAIL_BACKEND`
- `DJANGO_PRO_MODE`

## Requirements

- Basic dependencies: `requirements-basic.txt`
- Pro dependencies: `requirements-pro.txt`

## Run (Windows PowerShell)

Basic mode example:

```powershell
$env:DJANGO_PRO_MODE = "False"
python manage.py runserver
```

Pro mode example:

```powershell
$env:DJANGO_PRO_MODE = "True"
$env:DJANGO_DEBUG = "False"
python manage.py runserver
```
