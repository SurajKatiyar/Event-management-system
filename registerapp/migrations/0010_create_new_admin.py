from django.db import migrations


def create_superuser(apps, schema_editor):
    User = apps.get_model("auth", "User")

    if not User.objects.filter(username="suraj_secure_admin").exists():
        User.objects.create_superuser(
            username="suraj_secure_admin",
            email="yourrealemail@gmail.com",
            password="StrongSecure@2026Admin"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("registerapp", "0007_registration_attendance_time_registration_attended"),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]