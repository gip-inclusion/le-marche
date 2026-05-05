from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0006_siae_decp_details_last_sync_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalsiae",
            name="tender_detail_not_interested_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de besoins refusés",
            ),
        ),
        migrations.AddField(
            model_name="siae",
            name="tender_detail_not_interested_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de besoins refusés",
            ),
        ),
    ]
