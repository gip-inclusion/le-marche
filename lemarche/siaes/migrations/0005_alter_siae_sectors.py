# Generated by Django 3.2.4 on 2021-09-08 13:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sectors", "0002_sector"),
        ("siaes", "0004_siae_networks"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siae",
            name="sectors",
            field=models.ManyToManyField(
                blank=True, related_name="siaes", to="sectors.Sector", verbose_name="Secteurs d'activité"
            ),
        ),
    ]
