# Generated by Django 3.2.4 on 2021-08-31 17:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0006_auto_20210902_1724"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="Siae",
                )
            ],
            database_operations=[
                migrations.AlterModelTable(
                    name="Siae",
                    table="siaes_siae",
                )
            ],
        )
    ]
