# Generated by Django 4.1.7 on 2023-05-31 16:34

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("labels", "0001_initial"),
        ("siaes", "0058_siaelabel_old"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiaeLabel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("logs", models.JSONField(default=list, editable=False, verbose_name="Logs historiques")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
                (
                    "label",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="labels.label",
                        verbose_name="Label & certification",
                    ),
                ),
                (
                    "siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="siaes.siae", verbose_name="Structure"
                    ),
                ),
            ],
            options={
                "verbose_name": "Label & certification",
                "verbose_name_plural": "Labels & certifications",
                "ordering": ["-created_at"],
            },
        ),
    ]
