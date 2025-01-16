from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.create(
        name="Dépôt de besoin : auteur : modifications requises",
        code="TENDERS_AUTHOR_MODIFICATION_REQUEST",
        description="Envoyé à l'auteur du besoin pour lui demander de le modifier ou de prendre rendez-vous avec les admins",
    )
    TemplateTransactional.objects.create(
        name="Dépôt de besoin : auteur : dépôt de besoin rejeté",
        code="TENDERS_AUTHOR_REJECT_MESSAGE",
        description="Envoyé à l'auteur du besoin pour l'informer du rejet de son dépôt de besoin",
    )


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.filter(code="TENDERS_AUTHOR_MODIFICATION_REQUEST").delete()
    TemplateTransactional.objects.filter(code="TENDERS_AUTHOR_REJECT_MESSAGE").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0018_conversation_is_anonymized"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
