import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0003_siae_decp_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiaePublicMarket",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "market_uid",
                    models.CharField(max_length=255, verbose_name="Identifiant du marché (uid DECP)"),
                ),
                ("buyer_name", models.CharField(blank=True, max_length=500, verbose_name="Acheteur")),
                ("market_object", models.TextField(blank=True, verbose_name="Objet du marché")),
                (
                    "amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=14, null=True, verbose_name="Montant"
                    ),
                ),
                (
                    "award_date",
                    models.DateField(blank=True, null=True, verbose_name="Date d'attribution"),
                ),
                (
                    "source_date_type",
                    models.CharField(
                        choices=[
                            ("dateNotification", "Date de notification"),
                            ("datePublicationDonnees", "Date de publication"),
                        ],
                        default="dateNotification",
                        max_length=30,
                        verbose_name="Source de la date",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
                (
                    "siae",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="public_markets",
                        to="siaes.siae",
                        verbose_name="Structure",
                    ),
                ),
            ],
            options={
                "verbose_name": "Marché public remporté",
                "verbose_name_plural": "Marchés publics remportés",
                "ordering": ["-award_date"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="siaepublicmarket",
            unique_together={("siae", "market_uid")},
        ),
    ]
