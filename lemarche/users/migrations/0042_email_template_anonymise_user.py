from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.create(
        name="Avertissement d'anonymisation de compte utilisateur",
        code="USER_ANONYMIZATION_WARNING",
        description="""
        Bonjour {{ params.user_full_name }}, votre compte va être supprimé le {{ params.anonymization_date }}
         si vous ne vous connectez pas avant.
        Bonne journée,
        L'équipe du marché de l'inclusion
        """,
    )


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.get(code="USER_ANONYMIZATION_WARNING").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0041_remove_user_image_name_remove_user_image_url"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
