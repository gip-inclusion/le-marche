# Generated by Django 4.0.4 on 2022-06-13 08:55

from django.db import migrations, models

import lemarche.utils.fields


class Migration(migrations.Migration):
    dependencies = [
        ("tenders", "0015_alter_partnersharetender_arrayfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="tender",
            name="presta_type",
            field=lemarche.utils.fields.ChoiceArrayField(
                base_field=models.CharField(
                    choices=[
                        ("DISP", "Mise à disposition - Interim"),
                        ("PREST", "Prestation de service"),
                        ("BUILD", "Fabrication et commercialisation de biens"),
                    ],
                    max_length=20,
                ),
                default=[],
                size=None,
                verbose_name="Type de prestation",
            ),
            preserve_default=False,
        ),
    ]
