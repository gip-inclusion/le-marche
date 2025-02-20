from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.get_or_create(
        code="TENDERS_AUTHOR_CONFIRMATION_VALIDATED",
        defaults={
            "name": "Confirmation de validation de besoin",
            "description": "Confirmation de validation de besoin",
        },
    )
    TemplateTransactional.objects.get_or_create(
        code="TENDERS_SIAE_PRESENTATION",
        defaults={"name": "Présentation du besoin au SIAE", "description": "Présentation du besoin au SIAE"},
    )


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0021_add_templatetransactional_tender_author_modification_request_and_reject_message"),
    ]

    operations = [
        migrations.RunPython(create_template, migrations.RunPython.noop),
    ]
