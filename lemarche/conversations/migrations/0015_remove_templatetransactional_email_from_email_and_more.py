# Generated by Django 4.2.9 on 2024-04-30 09:57

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("conversations", "0014_alter_templatetransactional_source"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="templatetransactional",
            name="email_from_email",
        ),
        migrations.RemoveField(
            model_name="templatetransactional",
            name="email_from_name",
        ),
        migrations.RemoveField(
            model_name="templatetransactional",
            name="email_subject",
        ),
    ]