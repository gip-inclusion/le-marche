# Generated by Django 4.1.7 on 2023-05-18 21:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0056_alter_siae_contact_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="siae",
            name="logs",
            field=models.JSONField(default=list, editable=False, verbose_name="Logs historiques"),
        ),
    ]
