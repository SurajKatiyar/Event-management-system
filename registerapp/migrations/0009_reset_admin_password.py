from django.db import migrations


def reset_admin_password(apps, schema_editor):
    User = apps.get_model("auth", "User")

    try:
        user = User.objects.get(username="suraj")
        user.set_password("@Admin2k26ofdjangoevent.")
        user.save()
    except User.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("registerapp", "0009_registration_attendance_time_registration_attended"),
    ]

    operations = [
        migrations.RunPython(reset_admin_password),
    ]