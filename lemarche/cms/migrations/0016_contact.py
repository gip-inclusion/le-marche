from django.db import migrations


def paragraph_migration(apps, schema_editor):
    Paragraph = apps.get_model("cms", "Paragraph")
    Paragraph.objects.create(
        title="Vous avez des question ?",
        slug="rdv-contact",
        content='<h4 data-block-key="2tu4c"><b>Vous avez des questions ?</h4><p data-block-key="3vo75">Contactez nous au<br/><b>06 66 66 66 66</b></p>',
    )


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0015_paragraph"),
    ]

    operations = [
        migrations.RunPython(paragraph_migration, migrations.RunPython.noop),
    ]
