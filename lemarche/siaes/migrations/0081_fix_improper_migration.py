"""
Fixes 0022_siae_users_m2m_add_through.py
The problem was that because of obscure SQL script ran into the migration,
an undeclared unique constraint persisted, without any trace of it on the model.
This led to mysterious integrity constraints errors.
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


def copy_trough_model_data(apps, schema_editor):
    """Copy data from SiaeUser to TEMP_SiaeUser"""
    old_siae_user_model = apps.get_model("siaes", "SiaeUser")
    new_siae_user_model = apps.get_model("siaes", "TEMP_SiaeUser")

    new_siae_user_list = []
    for old_siae_user in old_siae_user_model.objects.all():
        new_siae_user_list.append(
            new_siae_user_model(
                siae=old_siae_user.siae,
                user=old_siae_user.user,
                created_at=old_siae_user.created_at,
                updated_at=old_siae_user.updated_at,
            )
        )
    new_siae_user_model.objects.bulk_create(new_siae_user_list)


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0080_remove_historicalsiae_is_cocontracting_and_more"),
    ]

    operations = [
        # Create a temporary Through model
        migrations.CreateModel(
            name="TEMP_SiaeUser",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                (
                    "siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="siaes.siae", verbose_name="Structure"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Date de modification"),
                ),
            ],
        ),
        # Create a temporary model field, linked to the temporary Through model
        migrations.AddField(
            model_name="siae",
            name="temp_users",
            field=models.ManyToManyField(
                blank=True,
                related_name="siaes",
                through="siaes.TEMP_SiaeUser",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Gestionnaires",
            ),
        ),
        # Copy the old through model data to the new one
        migrations.RunPython(copy_trough_model_data, migrations.RunPython.noop),
        # Remove old SiaeUser and associated fields
        migrations.RemoveField(model_name="siae", name="users"),
        migrations.DeleteModel("SiaeUser"),
        # Rename new TEMP_SiaeUser to override the old one
        migrations.RenameField(
            model_name="siae",
            old_name="temp_users",
            new_name="users",
        ),
        migrations.RenameModel(
            old_name="TEMP_SiaeUser",
            new_name="SiaeUser",
        ),
    ]
