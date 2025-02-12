# Generated by Django 4.2.15 on 2024-12-11 17:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_email_groups(apps, schema_editor):
    # Get the model
    EmailGroup = apps.get_model("conversations", "EmailGroup")

    # Create email groups
    email_groups = [
        {
            "id": 1,
            "display_name": "Structure(s) intéressée(s)",
            "description": "En désactivant cette option, vous ne serez plus averti par email lorsque des fournisseurs s'intéressent à votre besoin, ce qui pourrait vous faire perdre des opportunités de collaboration rapide et efficace.",
            "relevant_user_kind": "BUYER",
            "can_be_unsubscribed": True,
        },
        {
            "id": 2,
            "display_name": "Communication marketing",
            "description": "En désactivant cette option, vous ne recevrez plus par email nos newsletters, enquêtes, invitations à des webinaires et Open Labs, ce qui pourrait vous priver d'informations utiles et de moments d'échange exclusifs.",
            "relevant_user_kind": "BUYER",
            "can_be_unsubscribed": True,
        },
        {
            "id": 3,
            "display_name": "Opportunités commerciales",
            "description": "En désactivant cette option, vous ne recevrez plus par email les demandes de devis et les appels d'offres spécialement adaptés à votre activité, ce qui pourrait vous faire manquer des opportunités importantes pour votre entreprise.",
            "relevant_user_kind": "SIAE",
            "can_be_unsubscribed": True,
        },
        {
            "id": 4,
            "display_name": "Demandes de mise en relation",
            "description": "En désactivant cette option, vous ne recevrez plus par email les demandes de mise en relation de clients intéressés par votre structure, ce qui pourrait vous faire perdre des opportunités précieuses de collaboration et de développement.",
            "relevant_user_kind": "SIAE",
            "can_be_unsubscribed": True,
        },
        {
            "id": 5,
            "display_name": "Communication marketing",
            "description": "En désactivant cette option, vous ne recevrez plus par email nos newsletters, enquêtes, invitations aux webinaires et Open Labs, ce qui pourrait vous faire passer à côté d’informations clés, de ressources utiles et d’événements exclusifs.",
            "relevant_user_kind": "SIAE",
            "can_be_unsubscribed": True,
        },
    ]

    for group in email_groups:
        EmailGroup.objects.create(**group)


def delete_email_groups(apps, schema_editor):
    # Get the model
    EmailGroup = apps.get_model("conversations", "EmailGroup")
    # Delete all email groups
    EmailGroup.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("conversations", "0016_templatetransactionalsendlog"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("display_name", models.CharField(blank=True, max_length=255, verbose_name="Nom")),
                ("description", models.TextField(blank=True, verbose_name="Description")),
                (
                    "relevant_user_kind",
                    models.CharField(
                        choices=[
                            ("SIAE", "Structure"),
                            ("BUYER", "Acheteur"),
                            ("PARTNER", "Partenaire"),
                            ("INDIVIDUAL", "Particulier"),
                        ],
                        default="BUYER",
                        max_length=20,
                        verbose_name="Type d'utilisateur",
                    ),
                ),
                (
                    "can_be_unsubscribed",
                    models.BooleanField(default=False, verbose_name="L'utilisateur peut s'y désinscrire"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DisabledEmail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("disabled_at", models.DateTimeField(auto_now_add=True)),
                (
                    "group",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="conversations.emailgroup"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="disabled_emails",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="templatetransactional",
            name="group",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to="conversations.emailgroup"
            ),
        ),
        migrations.AddConstraint(
            model_name="disabledemail",
            constraint=models.UniqueConstraint(models.F("user"), models.F("group"), name="unique_group_per_user"),
        ),
        migrations.RunPython(create_email_groups, delete_email_groups),
    ]
