# Generated by Django 4.0.2 on 2022-03-14 18:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sectors", "0003_sector_sectorgroup_ordering"),
        ("siaes", "0050_siae_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="siaegroup",
            name="sectors",
            field=models.ManyToManyField(
                blank=True, related_name="siae_groups", to="sectors.Sector", verbose_name="Secteurs d'activité"
            ),
        ),
    ]
