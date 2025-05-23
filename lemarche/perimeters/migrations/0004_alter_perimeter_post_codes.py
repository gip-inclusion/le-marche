# Generated by Django 3.2.8 on 2021-11-22 17:53

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("perimeters", "0003_avoid_null_on_charfields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="perimeter",
            name="post_codes",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=5),
                blank=True,
                default=list,
                size=None,
                verbose_name="Codes postaux",
            ),
        ),
    ]
