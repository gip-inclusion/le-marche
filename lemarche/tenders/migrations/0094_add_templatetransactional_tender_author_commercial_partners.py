from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.create(
        name="Dépôt de besoin : auteur : notification quand son besoin a été validé et pris en charge par les partenaires commerciaux",
        code="TENDERS_AUTHOR_CONFIRMATION_VALIDATED_COMMERCIAL_PARTNERS",
        description="Envoyé à l'auteur du besoin lorsque son besoin a été validé et qu'il n'est pas envoyé aux structures mais proposé aux partenaires commerciaux",
    )


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.get(code="TENDERS_AUTHOR_CONFIRMATION_VALIDATED_COMMERCIAL_PARTNERS").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0093_alter_tender_send_to_commercial_partners_only"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
