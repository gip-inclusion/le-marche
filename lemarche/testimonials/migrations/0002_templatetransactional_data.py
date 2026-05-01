from django.db import migrations


def add_testimonial_templates(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.get_or_create(
        code="TESTIMONIAL_REQUEST",
        defaults={
            "name": "Invitation témoignage client",
            "description": "Email envoyé au client pour l'inviter à déposer un témoignage sur la structure.",
            "brevo_id": 478,
            "is_active": True,
        },
    )
    TemplateTransactional.objects.get_or_create(
        code="TESTIMONIAL_RECEIVED",
        defaults={
            "name": "Nouveau témoignage reçu",
            "description": "Email envoyé aux membres de la structure quand un client soumet un témoignage.",
            "brevo_id": 479,
            "is_active": True,
        },
    )


def remove_testimonial_templates(apps, schema_editor):
    TemplateTransactional = apps.get_model("conversations", "TemplateTransactional")
    TemplateTransactional.objects.filter(code__in=["TESTIMONIAL_REQUEST", "TESTIMONIAL_RECEIVED"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("testimonials", "0001_initial"),
        ("conversations", "0004_add_buyer_ao_email_template"),
    ]

    operations = [
        migrations.RunPython(add_testimonial_templates, reverse_code=remove_testimonial_templates),
    ]
