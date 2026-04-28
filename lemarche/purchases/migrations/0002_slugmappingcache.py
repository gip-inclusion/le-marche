import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchases", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SlugMappingCache",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("raw_value", models.CharField(db_index=True, max_length=255, verbose_name="Valeur saisie")),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("sector", "Secteur d'activité"),
                            ("perimeter", "Périmètre géographique"),
                            ("column_header", "En-tête de colonne"),
                        ],
                        max_length=30,
                        verbose_name="Type",
                    ),
                ),
                ("resolved_slug", models.CharField(max_length=255, verbose_name="Slug résolu")),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("user_proposed", "Proposé par un utilisateur"),
                            ("admin_validated", "Validé par un administrateur"),
                            ("auto_trigram", "Résolu automatiquement (trigram)"),
                        ],
                        default="user_proposed",
                        max_length=30,
                        verbose_name="Source",
                    ),
                ),
                ("confidence", models.FloatField(default=1.0, verbose_name="Score de confiance")),
                ("usage_count", models.PositiveIntegerField(default=1, verbose_name="Nombre d'utilisations")),
                (
                    "proposed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="slug_mapping_proposals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Proposé par",
                    ),
                ),
                (
                    "validated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="slug_mapping_validations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Validé par",
                    ),
                ),
                ("validated_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
            ],
            options={
                "verbose_name": "Correspondance de matching",
                "verbose_name_plural": "Correspondances de matching",
                "ordering": ["-usage_count", "raw_value"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="slugmappingcache",
            unique_together={("raw_value", "kind")},
        ),
    ]
