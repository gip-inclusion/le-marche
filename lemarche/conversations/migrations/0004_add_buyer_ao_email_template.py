from django.db import migrations


def create_buyer_ao_email_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")

    TemplateTransactional.objects.create(
        name="Besoin : acheteur : envoi appel d'offres à prestataires sélectionnés",
        code="TENDERS_BUYER_AO_EMAIL",
        description="Envoyé par un acheteur à des prestataires sélectionnés depuis son tableau de sourcing.",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0003_add_user_deletion_warning_template"),
    ]

    operations = [migrations.RunPython(create_buyer_ao_email_template, reverse_code=migrations.RunPython.noop)]
