from django.db import migrations

from lemarche.tenders.constants import STATUS_REJECTED


def update_rejected_tenders(apps, schema_editor):
    """Before we set up the Tender status system, Tender title were prefixed with 'HS xxxxx'
    to mark them as non-pertinent.
    Here we update the prefixed tenders with the rejected status"""
    Tender = apps.get_model("tenders", "Tender")
    Tender.objects.filter(title__startswith="HS ").update(status=STATUS_REJECTED)


class Migration(migrations.Migration):

    dependencies = [
        ("tenders", "0097_questionanswer"),
    ]

    operations = [
        migrations.RunPython(
            update_rejected_tenders,
            migrations.RunPython.noop,
        )
    ]
