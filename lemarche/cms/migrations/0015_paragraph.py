# Generated by Django 5.1.6 on 2025-02-18 09:33

import wagtail.fields
from django.db import migrations, models


def paragraph_migration(apps, schema_editor):
    Paragraph = apps.get_model("cms", "Paragraph")
    Paragraph.objects.create(
        title="Prise de rendez vous", slug="rdv-signup", content="Prenez un rendez vous s'il vous plaît"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0014_homepage_sub_header_custom_message"),
    ]

    operations = [
        migrations.CreateModel(
            name="Paragraph",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255, verbose_name="Titre de l'encart")),
                (
                    "slug",
                    models.SlugField(unique=True, help_text="Identifiant", max_length=255, verbose_name="slug"),
                ),
                ("content", wagtail.fields.RichTextField(blank=True, verbose_name="Contenu")),
            ],
            options={
                "verbose_name": "Paragraphe",
                "verbose_name_plural": "Paragraphes",
            },
        ),
        migrations.RunPython(paragraph_migration, migrations.RunPython.noop),
    ]
