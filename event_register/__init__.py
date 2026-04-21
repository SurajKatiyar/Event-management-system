from django.db import migrations


def create_superuser(apps, schema_editor):
    User = apps.get_model("auth", "User")

    if not User.objects.filter(username="surajadmin").exists():
        User.objects.create_superuser(
            username="surajadmin",
            email="surajkatiyar753@gmail.com",
            password="@Admindjango2k26pass."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("registerapp", "0007_registration_attendance_time_registration_attended"),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]