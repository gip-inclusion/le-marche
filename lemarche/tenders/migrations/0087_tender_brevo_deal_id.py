# Generated by Django 4.2.9 on 2024-05-03 09:40

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0086_alter_tender_limit_nb_siae_interested"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="brevo_deal_id",
            field=models.CharField(blank=True, max_length=80, null=True, verbose_name="Brevo deal id"),
        ),
    ]
