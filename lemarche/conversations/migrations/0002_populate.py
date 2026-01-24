from django.db import migrations


def create_template(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")

    # List of Tally templates to create
    templates = [
        {
            "name": "Dépôt de besoin : auteur : modifications requises",
            "code": "TENDERS_AUTHOR_MODIFICATION_REQUEST",
            "description": "Envoyé à l'auteur du besoin pour lui demander de le modifier ou de prendre rendez-vous "
            "avec les admins",
        },
        {
            "name": "Dépôt de besoin : auteur : dépôt de besoin rejeté",
            "code": "TENDERS_AUTHOR_REJECT_MESSAGE",
            "description": "Envoyé à l'auteur du besoin pour l'informer du rejet de son dépôt de besoin",
        },
        {
            "name": "Avertissement d'anonymisation de compte utilisateur",
            "code": "USER_ANONYMIZATION_WARNING",
            "description": """
        Bonjour {{ params.user_full_name }}, votre compte va être supprimé le {{ params.anonymization_date }}
         si vous ne vous connectez pas avant.
        Bonne journée,
        L'équipe du marché de l'inclusion
        """,
        },
        {
            "name": "Confirmation de l'onboarding",
            "code": "USER_ONBOARDING_CONFIRMED",
            "description": "Vous avez été onboardé, vous pouvez mainteant profiter des toutes les fonctionalités",
        },
        {
            "code": "TENDERS_AUTHOR_CONFIRMATION_VALIDATED",
            "name": "Confirmation de validation de besoin",
            "description": "Confirmation de validation de besoin",
        },
        {
            "code": "TENDERS_SIAE_PRESENTATION",
            "name": "Présentation du besoin au SIAE",
            "description": "Présentation du besoin au SIAE",
        },
        {
            "code": "TENDERS_AUTHOR_SIAE_INTERESTED_1",
            "name": "Notification de SIAE interessé",
            "description": "Notification de SIAE interessé",
        },
        {
            "code": "TENDERS_AUTHOR_SIAE_INTERESTED_2",
            "name": "Notification de SIAE interessé",
            "description": "Notification de SIAE interessé",
        },
        {
            "code": "TENDERS_AUTHOR_SIAE_INTERESTED_5",
            "name": "Notification de SIAE interessé",
            "description": "Notification de SIAE interessé",
        },
        {
            "code": "TENDERS_AUTHOR_SIAE_INTERESTED_5_MORE",
            "name": "Notification de SIAE interessé",
            "description": "Notification de SIAE interessé",
        },
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
        {
            "name": "Dépôt de besoin : auteur : notification quand son besoin a été validé et pris en charge par "
            "les partenaires commerciaux",
            "code": "TENDERS_AUTHOR_CONFIRMATION_VALIDATED_COMMERCIAL_PARTNERS",
            "description": "Envoyé à l'auteur du besoin lorsque son besoin a été validé et qu'il n'est pas envoyé"
            " aux structures mais proposé aux partenaires commerciaux",
        },
    ]

    # Create all templates
    templates = [TemplateTransactional(**template) for template in templates]
    TemplateTransactional.objects.bulk_create(templates)


def create_email_groups(apps, schema_editor):
    # Get the model
    EmailGroup = apps.get_model("conversations", "EmailGroup")

    # Create email groups
    email_groups = [
        {
            "display_name": "Structure(s) intéressée(s)",
            "description": "En désactivant cette option, vous ne serez plus averti par email lorsque des fournisseurs"
            " s'intéressent à votre besoin, ce qui pourrait vous faire perdre des opportunités de"
            " collaboration rapide et efficace.",
            "relevant_user_kind": "BUYER",
            "can_be_unsubscribed": True,
        },
        {
            "display_name": "Communication marketing",
            "description": "En désactivant cette option, vous ne recevrez plus par email nos newsletters, enquêtes,"
            " invitations à des webinaires et Open Labs, ce qui pourrait vous priver d'informations"
            " utiles et de moments d'échange exclusifs.",
            "relevant_user_kind": "BUYER",
            "can_be_unsubscribed": True,
        },
        {
            "display_name": "Opportunités commerciales",
            "description": "En désactivant cette option, vous ne recevrez plus par email les demandes de devis et"
            " les appels d'offres spécialement adaptés à votre activité, ce qui pourrait vous faire"
            " manquer des opportunités importantes pour votre entreprise.",
            "relevant_user_kind": "SIAE",
            "can_be_unsubscribed": True,
        },
        {
            "display_name": "Demandes de mise en relation",
            "description": "En désactivant cette option, vous ne recevrez plus par email les demandes de mise en"
            " relation de clients intéressés par votre structure, ce qui pourrait vous faire perdre"
            " des opportunités précieuses de collaboration et de développement.",
            "relevant_user_kind": "SIAE",
            "can_be_unsubscribed": True,
        },
        {
            "display_name": "Communication marketing",
            "description": "En désactivant cette option, vous ne recevrez plus par email nos newsletters, enquêtes,"
            " invitations aux webinaires et Open Labs, ce qui pourrait vous faire passer à côté"
            " d’informations clés, de ressources utiles et d’événements exclusifs.",
            "relevant_user_kind": "SIAE",
            "can_be_unsubscribed": True,
        },
    ]

    for group in email_groups:
        EmailGroup.objects.create(**group)


class Migration(migrations.Migration):
    replaces = [
        ("conversations", "0021_add_templatetransactional_tender_author_modification_request_and_reject_message")
    ]

    dependencies = [
        ("conversations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_template, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(create_email_groups, reverse_code=migrations.RunPython.noop),
    ]
