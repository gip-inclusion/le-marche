# Generated by Django 4.2.2 on 2023-11-27 15:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0066_siae_etablissement_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="siae",
            name="completion_rate",
            field=models.IntegerField(blank=True, null=True, verbose_name="Taux de remplissage de sa fiche"),
        ),
    ]
