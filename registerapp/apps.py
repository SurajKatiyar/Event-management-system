from django.apps import AppConfig


class RegisterappConfig(AppConfig):
    name = "registerapp"

    def ready(self):
        import os
        from django.contrib.auth import get_user_model

        User = get_user_model()

        admin_username = os.getenv("surajadmin")
        admin_email = os.getenv("surajkatiyar753@gmail.com")
        admin_password = os.getenv("@Admindjango2k26pass.")

        if admin_username and admin_password:
            if not User.objects.filter(username=admin_username).exists():
                User.objects.create_superuser(
                    username=admin_username,
                    email=admin_email,
                    password=admin_password
                )