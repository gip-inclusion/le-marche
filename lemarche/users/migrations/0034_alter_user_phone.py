# Generated by Django 4.2.13 on 2024-05-15 13:55

import phonenumber_field.modelfields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0033_user_brevo_contact_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="phone",
            field=phonenumber_field.modelfields.PhoneNumberField(
                blank=True, max_length=20, region=None, verbose_name="Téléphone"
            ),
        ),
    ]