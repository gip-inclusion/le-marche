# Generated by Django 3.2.7 on 2021-09-15 13:15

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0005_alter_user_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="c4_id",
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_company_name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Nom de l'entreprise"),
        ),
        migrations.AddField(
            model_name="user",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="Date de création"),
        ),
        migrations.AddField(
            model_name="user",
            name="kind",
            field=models.CharField(
                choices=[
                    ("SIAE", "SIAE"),
                    ("BUYER", "Acheteur (classique)"),
                    ("PARTNER", "Partenaire"),
                    ("ADMIN", "Administrateur"),
                ],
                max_length=20,
                verbose_name="Type",
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="phone",
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name="Téléphone"),
        ),
        migrations.AddField(
            model_name="user",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_website",
            field=models.URLField(blank=True, null=True, verbose_name="Site web"),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, unique=True, verbose_name="E-mail"),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(max_length=150, verbose_name="Prénom"),
        ),
        migrations.AlterField(
            model_name="user",
            name="last_name",
            field=models.CharField(max_length=150, verbose_name="Nom"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_siret",
            field=models.CharField(blank=True, max_length=14, null=True, verbose_name="Siret ou Siren"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_naf",
            field=models.CharField(blank=True, max_length=5, null=True, verbose_name="Naf"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_accept_rgpd",
            field=models.BooleanField(default=False, help_text="J'accepte les conditions d'utilisation du service"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_accept_survey",
            field=models.BooleanField(
                default=False,
                help_text="J'accepte de répondre à une enquête deux fois par an afin de permettre de mesurer la progression des achats inclusifs en France",  # noqa
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_email_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_id_card_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_offers_for_pro_sector",
            field=models.BooleanField(
                default=False,
                help_text="Je m'engage à ce que les offres déposées sur la Place de marché soient destinées à des structures professionnelles (association, secteur privé ou public)",  # noqa
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_phone_prefix",
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name="Indicatif international"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_time_zone",
            field=models.CharField(blank=True, max_length=150, null=True, verbose_name="Fuseau"),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_phone_verified",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="c4_quote_promise",
            field=models.BooleanField(
                default=False,
                help_text="Je m'engage à traiter les demandes de devis qui me seront adressées (soumettre un devis, solliciter des informations complémentaires ou  refuser une demande constituent des réponses)",  # noqa
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="api_key",
            field=models.CharField(blank=True, max_length=128, null=True, unique=True, verbose_name="Clé API"),
        ),
    ]
