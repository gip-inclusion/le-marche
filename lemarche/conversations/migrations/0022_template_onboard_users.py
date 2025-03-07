from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.create(
        name="Confirmation de l'onboarding",
        code="USER_ONBOARDING_CONFIRMED",
        description="Vous avez été onboardé, vous pouvez mainteant profiter des toutes les fonctionalités",
    )


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.filter(code="USER_ONBOARDING_CONFIRMED").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0021_add_templatetransactional_tender_author_modification_request_and_reject_message"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
