# Generated by Django 4.2.9 on 2024-03-06 08:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0078_tender_admins"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="siae_transactioned_last_updated",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="Abouti à une transaction : date de mise à jour"
            ),
        ),
    ]