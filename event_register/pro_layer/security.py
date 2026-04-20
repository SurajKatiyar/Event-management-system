import os


def _to_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _split_csv(value):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def apply_pro_security(settings_dict):
    """Apply hardened settings in pro mode without changing the basic setup."""
    secure_proxy_header = os.getenv("SECURE_PROXY_SSL_HEADER", "HTTP_X_FORWARDED_PROTO,https")
    if "," in secure_proxy_header:
        header_name, header_value = secure_proxy_header.split(",", 1)
        settings_dict["SECURE_PROXY_SSL_HEADER"] = (header_name.strip(), header_value.strip())

    settings_dict["DEBUG"] = False
    settings_dict["SECURE_SSL_REDIRECT"] = _to_bool(os.getenv("SECURE_SSL_REDIRECT"), True)
    settings_dict["SESSION_COOKIE_SECURE"] = _to_bool(os.getenv("SESSION_COOKIE_SECURE"), True)
    settings_dict["CSRF_COOKIE_SECURE"] = _to_bool(os.getenv("CSRF_COOKIE_SECURE"), True)
    settings_dict["SECURE_HSTS_SECONDS"] = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    settings_dict["SECURE_HSTS_INCLUDE_SUBDOMAINS"] = _to_bool(os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS"), True)
    settings_dict["SECURE_HSTS_PRELOAD"] = _to_bool(os.getenv("SECURE_HSTS_PRELOAD"), True)
    settings_dict["SECURE_CONTENT_TYPE_NOSNIFF"] = _to_bool(os.getenv("SECURE_CONTENT_TYPE_NOSNIFF"), True)
    settings_dict["X_FRAME_OPTIONS"] = os.getenv("X_FRAME_OPTIONS", "DENY")
    settings_dict["CSRF_TRUSTED_ORIGINS"] = _split_csv(os.getenv("CSRF_TRUSTED_ORIGINS", ""))

    allowed_hosts = _split_csv(os.getenv("DJANGO_ALLOWED_HOSTS", ""))
    if allowed_hosts:
        settings_dict["ALLOWED_HOSTS"] = allowed_hosts

    settings_dict["EMAIL_BACKEND"] = os.getenv(
        "DJANGO_EMAIL_BACKEND",
        "django.core.mail.backends.smtp.EmailBackend",
    )

    settings_dict["LOGGING"] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[{asctime}] {levelname} {name} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
        },
    }
