from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0003_tender_siae_groupement_and_referent_regional"),
    ]

    operations = [
        migrations.AddField(
            model_name="referentregional",
            name="logo",
            field=models.FileField(
                blank=True,
                help_text="Logo du réseau (GRAFIE, GESAT…). Affiché dans 'Besoin d'aide ?' (page groupement).",
                null=True,
                upload_to="referents_regionaux/logos/",
                verbose_name="Logo du réseau régional",
            ),
        ),
    ]
