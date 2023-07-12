# Generated by Django 4.2.2 on 2023-07-12 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenders", "0050_alter_tender_source"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="notes",
            field=models.TextField(
                blank=True, help_text="Champ renseigné par un ADMIN", verbose_name="Notes à propos du besoin"
            ),
        ),
    ]