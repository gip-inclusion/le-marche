from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")

    # List of Tally templates to create
    templates = [
        {
            "name": "Tally : Utilisateur : Onboarding confirmé",
            "code": "TALLY_USER_ONBOARDING_CONFIRMED",
            "description": "Template Tally pour confirmer l'onboarding d'un utilisateur",
        },
        {
            "name": "Tally : Besoin : Présentation SIAE",
            "code": "TALLY_TENDERS_SIAE_PRESENTATION",
            "description": "Template Tally pour la présentation d'une SIAE",
        },
        {
            "name": "Tally : Besoin : Auteur : 1 SIAE intéressée",
            "code": "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_1",
            "description": "Template Tally envoyé à l'auteur du besoin quand 1 SIAE est intéressée",
        },
        {
            "name": "Tally : Besoin : Auteur : 2 SIAE intéressées",
            "code": "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_2",
            "description": "Template Tally envoyé à l'auteur du besoin quand 2 SIAE sont intéressées",
        },
        {
            "name": "Tally : Besoin : Auteur : 5 SIAE intéressées",
            "code": "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_5",
            "description": "Template Tally envoyé à l'auteur du besoin quand 5 SIAE sont intéressées",
        },
        {
            "name": "Tally : Besoin : Auteur : Plus de 5 SIAE intéressées",
            "code": "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_MORE",
            "description": "Template Tally envoyé à l'auteur du besoin quand plus de 5 SIAE sont intéressées",
        },
        {
            "name": "Tally : Besoin : Auteur : Question transactionnelle 7 jours",
            "code": "TALLY_TENDERS_AUTHOR_TRANSACTIONED_QUESTION_7D",
            "description": "Template Tally pour les questions transactionnelles après 7 jours",
        },
        {
            "name": "Tally : Besoin : Auteur : Feedback 30 jours",
            "code": "TALLY_TENDERS_AUTHOR_FEEDBACK_30D",
            "description": "Template Tally pour le feedback après 30 jours",
        },
        {
            "name": "Tally : Besoin : Auteur : Modifications requises",
            "code": "TALLY_TENDERS_AUTHOR_MODIFICATION_REQUEST",
            "description": "Template Tally envoyé à l'auteur du besoin pour lui demander de le modifier",
        },
        {
            "name": "Tally : Besoin : Auteur : Besoin rejeté",
            "code": "TALLY_TENDERS_AUTHOR_REJECT_MESSAGE",
            "description": "Template Tally envoyé à l'auteur du besoin pour l'informer du rejet",
        },
        {
            "name": "Tally : Besoin : Auteur : Super SIAE",
            "code": "TALLY_TENDERS_AUTHOR_SUPER_SIAES",
            "description": "Template Tally envoyé à l'auteur du besoin concernant les super SIAE",
        },
    ]

    # Create all templates
    templates = [TemplateTransactional(**template) for template in templates]
    TemplateTransactional.objects.bulk_create(templates)


def delete_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")

    # Delete all created Tally templates
    template_codes = [
        "TALLY_USER_ONBOARDING_CONFIRMED",
        "TALLY_TENDERS_SIAE_PRESENTATION",
        "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_1",
        "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_2",
        "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_5",
        "TALLY_TENDERS_AUTHOR_SIAE_INTERESTED_MORE",
        "TALLY_TENDERS_AUTHOR_TRANSACTIONED_QUESTION_7D",
        "TALLY_TENDERS_AUTHOR_FEEDBACK_30D",
        "TALLY_TENDERS_AUTHOR_MODIFICATION_REQUEST",
        "TALLY_TENDERS_AUTHOR_REJECT_MESSAGE",
        "TALLY_TENDERS_AUTHOR_SUPER_SIAES",
    ]

    TemplateTransactional.objects.filter(code__in=template_codes).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0024_alter_templatetransactional_code"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=delete_template),
    ]
