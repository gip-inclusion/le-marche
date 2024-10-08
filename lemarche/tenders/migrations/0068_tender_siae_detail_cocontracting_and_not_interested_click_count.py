# Generated by Django 4.2.9 on 2024-01-16 16:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0067_tendersiae_detail_not_interested_click_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="siae_detail_cocontracting_click_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures ouvertes à la co-traitance",
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="siae_detail_not_interested_click_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures pas intéressées",
            ),
        ),
    ]
