# Generated by Django 3.2.4 on 2021-09-02 16:51

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0003_siae_add_missing_fields_update_others"),
        ("networks", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="siae",
            name="networks",
            field=models.ManyToManyField(
                blank=True, related_name="siaes", to="networks.Network", verbose_name="Réseaux"
            ),
        ),
    ]
