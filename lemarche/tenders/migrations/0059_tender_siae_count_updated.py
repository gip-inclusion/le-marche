# Generated by Django 4.2.2 on 2023-10-25 11:48

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0058_tenderstepsdata"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="siae_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures concernées",
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="siae_detail_contact_click_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures intéressées",
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="siae_detail_display_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures vues",
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="siae_email_link_click_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures cliquées",
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="siae_email_link_click_or_detail_display_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures cliquées ou vues",
            ),
        ),
        migrations.AddField(
            model_name="tender",
            name="siae_email_send_count",
            field=models.IntegerField(
                default=0,
                help_text="Champ recalculé à intervalles réguliers",
                verbose_name="Nombre de structures contactées",
            ),
        ),
    ]
