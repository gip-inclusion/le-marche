# Generated by Django 5.1.6 on 2025-05-05 15:42

import django.db.models.deletion
from django.db import migrations, models


def restore_restaurants(apps, schema_editor):
    """'restauration' group was deleted inadvertently, but sector_group field were supposed to always have a value,
    even if the model was made with non-nullable fields"""
    SiaeActivity = apps.get_model("siaes", "SiaeActivity")
    Sector = apps.get_model("sectors", "Sector")
    SectorGroup = apps.get_model("sectors", "SectorGroup")
    try:
        restau = SectorGroup.objects.get(slug="restauration")
        SiaeActivity.objects.filter(sector_group__isnull=True).update(sector_group=restau)
        Sector.objects.filter(group__isnull=True).update(group=restau)
    except SectorGroup.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("sectors", "0004_alter_sector_group"),
        ("siaes", "0085_alter_siaeactivity_presta_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="siaeactivity",
            name="sector_group",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="siae_activities",
                to="sectors.sectorgroup",
                verbose_name="Secteur d'activité",
            ),
        ),
        migrations.RunPython(restore_restaurants, migrations.RunPython.noop),
    ]
