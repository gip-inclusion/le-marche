# Generated by Django 3.2.4 on 2021-08-31 17:11

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("siaes", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL("alter sequence api_siae_id_seq rename to siaes_siae_id_seq;"),
        migrations.RunSQL("alter index api_siae_pkey rename to siaes_siae_pkey;"),
        migrations.RunSQL("alter index api_siae_siret_9098cdd1 rename to siaes_siae_siret_9098cdd1;"),
        migrations.RunSQL("alter index api_siae_siret_9098cdd1_like rename to siaes_siae_siret_9098cdd1_like;"),
    ]
