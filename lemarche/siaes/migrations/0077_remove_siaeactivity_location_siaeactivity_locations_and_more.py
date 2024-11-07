# Generated by Django 4.2.15 on 2024-10-07 14:03

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("perimeters", "0005_alter_perimeter_post_codes"),
        ("siaes", "0076_siaeactivity"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="siaeactivity",
            name="location",
        ),
        migrations.AddField(
            model_name="siaeactivity",
            name="locations",
            field=models.ManyToManyField(
                blank=True, related_name="siae_activities", to="perimeters.perimeter", verbose_name="Localisations"
            ),
        ),
        migrations.AlterField(
            model_name="siaeactivity",
            name="geo_range",
            field=models.CharField(
                blank=True,
                choices=[
                    ("COUNTRY", "France entière"),
                    ("CUSTOM", "Distance en kilomètres"),
                    ("ZONES", "Zone(s) d'intervention personnalisée(s)"),
                ],
                db_index=True,
                max_length=20,
                verbose_name="Périmètre d'intervention",
            ),
        ),
    ]