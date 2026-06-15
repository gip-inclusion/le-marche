from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("purchases", "0003_purchaseimport"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchaseimport",
            name="file",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="purchases/imports/",
                verbose_name="Fichier Excel",
            ),
        ),
    ]
