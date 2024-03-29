# Generated by Django 4.2.9 on 2024-02-14 16:14

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0074_alter_tender_siae_kind"),
    ]

    operations = [
        migrations.AddField(
            model_name="partnersharetender",
            name="is_active",
            field=models.BooleanField(
                default=False,
                verbose_name="Partenaire actif",
                help_text="Souhaite recevoir les besoins d'achats par email",
            ),
        ),
    ]
