import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0001_initial"),
        ("purchases", "0002_slugmappingcache"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PurchaseImport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "file",
                    models.FileField(upload_to="purchases/imports/", verbose_name="Fichier Excel"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "En attente"),
                            ("SUCCESS", "Terminée"),
                            ("FAILED", "Échouée"),
                        ],
                        default="PENDING",
                        max_length=20,
                        verbose_name="Statut",
                    ),
                ),
                ("year", models.PositiveIntegerField(verbose_name="Année des achats")),
                ("total_rows", models.PositiveIntegerField(default=0, verbose_name="Lignes traitées")),
                ("matched_rows", models.PositiveIntegerField(default=0, verbose_name="Structures reconnues")),
                ("error_message", models.TextField(blank=True, verbose_name="Message d'erreur")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="purchase_imports",
                        to="companies.company",
                        verbose_name="Entreprise",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="purchase_imports",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Importé par",
                    ),
                ),
            ],
            options={
                "verbose_name": "Import de dépenses",
                "verbose_name_plural": "Imports de dépenses",
                "ordering": ["-created_at"],
            },
        ),
    ]
