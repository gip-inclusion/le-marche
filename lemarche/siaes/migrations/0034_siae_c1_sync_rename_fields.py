# Generated by Django 3.2.8 on 2021-11-18 15:54

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0033_alter_siae_contact_email"),
    ]

    operations = [
        migrations.RenameField(
            model_name="siae",
            old_name="last_sync_date",
            new_name="c1_last_sync_date",
        ),
        migrations.RenameField(
            model_name="siae",
            old_name="sync_skip",
            new_name="c1_sync_skip",
        ),
    ]
