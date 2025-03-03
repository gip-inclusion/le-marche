from django.db import migrations
from django.db.models import Count, OuterRef, Subquery


def migrate_siaeactivity_sectors(apps, schema_editor):
    SiaeActivity = apps.get_model("siaes", "SiaeActivity")
    Sector = apps.get_model("sectors", "Sector")
    qs = SiaeActivity.objects.annotate(sector_count=Count("sectors")).filter(sector_count__gt=1)
    for siae_activity in qs:
        siae_activity.sector = siae_activity.sectors.first()
        for sector in siae_activity.sectors.all()[1:]:
            new_siae_activity = SiaeActivity.objects.create(
                siae=siae_activity.siae,
                sector=sector,
                presta_type=siae_activity.presta_type,
                geo_range=siae_activity.geo_range,
                geo_range_custom_distance=siae_activity.geo_range_custom_distance,
                created_at=siae_activity.created_at,
                updated_at=siae_activity.updated_at,
            )
            new_siae_activity.locations.set(siae_activity.locations.all())
    sector_subquery = Sector.objects.filter(siae_activities=OuterRef("pk"))
    qs = (
        SiaeActivity.objects.annotate(sector_count=Count("sectors"))
        .filter(sector_count=1)
        .update(sector=Subquery(sector_subquery.values("pk")[:1]))
    )


class Migration(migrations.Migration):

    dependencies = [
        ("sectors", "0003_sector_sectorgroup_ordering"),
        ("siaes", "0086_remove_siaeactivity_sectors_siaeactivity_sector"),
    ]

    operations = [
        migrations.RunPython(
            migrate_siaeactivity_sectors,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="siaeactivity",
            name="sectors",
        ),
    ]
