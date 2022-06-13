import io

from django.core.management import call_command
from django.db import connection


def reset_app_sql_sequences(app_name):
    """
    To reset the id indexes of a given app (will impact *all* of the apps' tables)
    https://docs.djangoproject.com/en/3.1/ref/django-admin/#sqlsequencereset
    https://stackoverflow.com/a/44113124
    """
    print(f"Resetting SQL sequences for {app_name}...")
    output = io.StringIO()
    call_command("sqlsequencereset", app_name, stdout=output, no_color=True)
    sql = output.getvalue()
    with connection.cursor() as cursor:
        cursor.execute(sql)
    output.close()
    print("Reset complete !")


def rename_dict_key(dict, key_name_before, key_name_after):
    dict[key_name_after] = dict[key_name_before]
    dict.pop(key_name_before)


def get_choice(choices, key):
    choices = dict(choices)
    if key in choices:
        return choices[key]
    return None
