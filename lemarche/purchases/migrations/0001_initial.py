# Generated by Django 5.1.6 on 2025-07-01 15:13

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("companies", "0005_company_linkedin_buyer_count"),
        ("siaes", "0089_delete_sectors"),
    ]

    operations = [
        migrations.CreateModel(
            name="Purchase",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "supplier_name",
                    models.CharField(
                        help_text="Nom de l'entreprise fournisseur",
                        max_length=255,
                        verbose_name="Raison sociale du Fournisseur",
                    ),
                ),
                (
                    "supplier_siret",
                    models.CharField(
                        help_text="Numéro SIRET du fournisseur (14 chiffres)",
                        max_length=14,
                        verbose_name="SIRET du Fournisseur",
                    ),
                ),
                (
                    "purchase_amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Montant de l'achat en euros",
                        max_digits=15,
                        verbose_name="Dépense achat (€)",
                    ),
                ),
                (
                    "purchase_category",
                    models.CharField(
                        blank=True,
                        help_text="Catégorie d'achat (optionnelle)",
                        max_length=255,
                        null=True,
                        verbose_name="Catégorie d'achat",
                    ),
                ),
                (
                    "buying_entity",
                    models.CharField(
                        blank=True,
                        help_text="Entité acheteuse (optionnelle)",
                        max_length=255,
                        null=True,
                        verbose_name="Entité acheteuse",
                    ),
                ),
                (
                    "purchase_year",
                    models.PositiveIntegerField(
                        help_text="Année de réalisation de l'achat", verbose_name="Année de l'achat"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
                ),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Date de modification")),
                (
                    "company",
                    models.ForeignKey(
                        help_text="Entreprise liée à l'achat",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="companies.company",
                        verbose_name="Entreprise",
                    ),
                ),
                (
                    "siae",
                    models.ForeignKey(
                        blank=True,
                        help_text="Structure d'insertion liée si le SIRET correspond",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="siaes.siae",
                        verbose_name="Structure d'insertion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Achat",
                "verbose_name_plural": "Achats",
                "indexes": [
                    models.Index(fields=["supplier_siret"], name="purchases_p_supplie_969a65_idx"),
                    models.Index(fields=["purchase_year"], name="purchases_p_purchas_86529c_idx"),
                ],
            },
        ),
    ]
