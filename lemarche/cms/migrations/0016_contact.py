from django.db import migrations


def paragraph_migration(apps, schema_editor):
    Paragraph = apps.get_model("cms", "Paragraph")
    Paragraph.objects.create(
        title="Vous avez des question ?", slug="rdv-contact", content="<p>Contactez nous au</p> <p> 06 66 66 66 66</p>"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0015_paragraph"),
    ]

    operations = [
        migrations.RunPython(paragraph_migration, migrations.RunPython.noop),
    ]
