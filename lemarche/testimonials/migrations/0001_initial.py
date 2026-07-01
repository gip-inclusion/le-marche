import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("siaes", "0006_siae_decp_details_last_sync_date"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SiaeTestimonial",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="testimonials",
                        to="siaes.siae",
                        verbose_name="Structure",
                    ),
                ),
                ("client_email", models.EmailField(verbose_name="Email du client")),
                ("custom_message", models.TextField(blank=True, verbose_name="Message personnalisé")),
                (
                    "token",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Token",
                    ),
                ),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="Date d'envoi")),
                (
                    "token_expires_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="Date d'expiration du token"),
                ),
                ("content", models.TextField(blank=True, max_length=500, verbose_name="Témoignage")),
                ("author_first_name", models.CharField(blank=True, max_length=255, verbose_name="Prénom de l'auteur")),
                ("author_last_name", models.CharField(blank=True, max_length=255, verbose_name="Nom de l'auteur")),
                (
                    "author_organization",
                    models.CharField(blank=True, max_length=100, verbose_name="Organisation de l'auteur"),
                ),
                (
                    "buyer_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="testimonials_given",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Utilisateur acheteur",
                    ),
                ),
                ("submitted_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de soumission")),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="Date de publication")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("SENT", "Invitation envoyée"),
                            ("SUBMITTED", "Soumis, en attente de validation"),
                            ("PUBLISHED", "Publié"),
                            ("REJECTED", "Rejeté"),
                        ],
                        db_index=True,
                        default="SENT",
                        max_length=20,
                        verbose_name="Statut",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
            ],
            options={
                "verbose_name": "Témoignage client",
                "verbose_name_plural": "Témoignages clients",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="siaetestimonial",
            unique_together={("siae", "client_email")},
        ),
    ]
