# Generated by Django 4.2.9 on 2024-02-09 14:47

from django.db import migrations, models

import lemarche.utils.fields


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0073_tendersiae_survey_transactioned_amount_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tender",
            name="siae_kind",
            field=lemarche.utils.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("EI", "Entreprise d'insertion"),
                        ("AI", "Association intermédiaire"),
                        ("ACI", "Atelier chantier d'insertion"),
                        ("ETTI", "Entreprise de travail temporaire d'insertion"),
                        ("EITI", "Entreprise d'insertion par le travail indépendant"),
                        ("GEIQ", "Groupement d'employeurs pour l'insertion et la qualification"),
                        ("SEP", "Produits et services réalisés en prison"),
                        ("EA", "Entreprise adaptée (EA)"),
                        ("EATT", "Entreprise adaptée de travail temporaire (EATT)"),
                        ("ESAT", "Etablissement et service d'aide par le travail (ESAT)"),
                    ],
                    max_length=20,
                ),
                blank=True,
                default=list,
                size=None,
                verbose_name="Type de structure",
            ),
        ),
    ]