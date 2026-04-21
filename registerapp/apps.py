from django.apps import AppConfig


class RegisterappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "registerapp"

    def ready(self):
        import os
        from django.contrib.auth import get_user_model

        User = get_user_model()

        username = os.getenv("ADMIN_USERNAME")
        email = os.getenv("ADMIN_EMAIL")
        password = os.getenv("ADMIN_PASSWORD")

        # create admin only if values exist
        if username and password:
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )