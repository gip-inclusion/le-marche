# Generated by Django 4.2.13 on 2024-06-26 13:11

from django.db import migrations


def remove_hubspot_deal_id(apps, schema_editor):
    Tender = apps.get_model("tenders", "Tender")
    for tender in Tender.objects.all():
        if "hubspot_deal_id" in tender.extra_data:
            del tender.extra_data["hubspot_deal_id"]
            tender.save()


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0089_tender_le_marche_doesnt_exist_how_to_find_siae"),
    ]

    operations = [
        migrations.RunPython(remove_hubspot_deal_id, migrations.RunPython.noop),
    ]