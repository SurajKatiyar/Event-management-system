from django.db import migrations


def reset_password(apps, schema_editor):
    User = apps.get_model("auth", "User")

    users = User.objects.filter(username="surajadmin")

    if users.exists():
        user = users.first()
        user.set_password("Suraj@Admin12345")
        user.is_staff = True
        user.is_superuser = True
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ("registerapp", "0007_registration_attendance_time_registration_attended"),
    ]

    operations = [
        migrations.RunPython(reset_password),
    ]