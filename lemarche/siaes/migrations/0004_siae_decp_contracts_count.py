from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0003_siae_decp_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalsiae",
            name="decp_contracts_count_last_3_years",
            field=models.IntegerField(
                default=0, verbose_name="Nombre de marchés publics remportés ces 3 dernières années (DECP)"
            ),
        ),
        migrations.AddField(
            model_name="siae",
            name="decp_contracts_count_last_3_years",
            field=models.IntegerField(
                default=0, verbose_name="Nombre de marchés publics remportés ces 3 dernières années (DECP)"
            ),
        ),
    ]
