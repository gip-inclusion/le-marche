# Generated by Django 4.2.2 on 2023-10-09 13:35

import django.utils.timezone
from django.db import migrations, models
from django_extensions.db.fields import ShortUUIDField
from shortuuid import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0057_alter_tender_siae_transactioned"),
    ]

    operations = [
        migrations.CreateModel(
            name="TenderStepsData",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "uuid",
                    ShortUUIDField(
                        auto_created=True,
                        blank=True,
                        db_index=True,
                        default=uuid,
                        editable=False,
                        unique=True,
                        verbose_name="Identifiant UUID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
                ("steps_data", models.JSONField(default=list, editable=False, verbose_name="Données des étapes")),
            ],
            options={
                "verbose_name": "Besoin d'achat - Données des étapes",
                "verbose_name_plural": "Besoins d'achat - Données des étapes",
            },
        ),
    ]
