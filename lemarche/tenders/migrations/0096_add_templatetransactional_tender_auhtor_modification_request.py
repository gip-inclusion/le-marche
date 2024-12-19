from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.create(
        name="Dépôt de besoin : auteur : modifications requises",
        code="TENDERS_AUTHOR_MODIFICATION_REQUEST",
        description="Envoyé à l'auteur du besoin pour lui demander de le modifier ou de prendre rendez-vous avec les admins",
    )


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.get(code="TENDERS_AUTHOR_MODIFICATION_REQUEST").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0095_tender_changes_information_and_more"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
