from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0002_alter_historicalsiae_name_alter_siae_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="siae",
            name="nudge_last_seen_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Date du dernier nudge de mise à jour de fiche"
            ),
        ),
    ]
