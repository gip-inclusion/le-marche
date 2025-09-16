from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.create(
        name="Relance des fournisseurs",
        code="SIAE_REMINDER",
        brevo_id=398,
        description="Template de relance pour les fournisseurs",
    )


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.filter(code="SIAE_REMINDER").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0025_add_tally_templatetransactional"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
