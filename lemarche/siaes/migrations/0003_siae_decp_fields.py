# Generated manually - run `python manage.py migrate` to apply

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0002_alter_historicalsiae_name_alter_siae_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="siae",
            name="has_won_contract_last_3_years",
            field=models.BooleanField(
                default=False,
                verbose_name="A remporté un marché public ces 3 dernières années (DECP)",
            ),
        ),
        migrations.AddField(
            model_name="siae",
            name="decp_last_sync_date",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Date de dernière synchronisation (DECP)",
            ),
        ),
    ]
