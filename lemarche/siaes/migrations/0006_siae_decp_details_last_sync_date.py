from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0005_siaepublicmarket"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalsiae",
            name="decp_details_last_sync_date",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Date de dernière synchronisation des détails DECP"
            ),
        ),
        migrations.AddField(
            model_name="siae",
            name="decp_details_last_sync_date",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Date de dernière synchronisation des détails DECP"
            ),
        ),
    ]
