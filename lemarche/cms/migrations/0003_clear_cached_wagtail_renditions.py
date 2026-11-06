from django.core.cache import DEFAULT_CACHE_ALIAS, InvalidCacheBackendError, caches
from django.db import migrations


def clear_cached_renditions(apps, schema_editor):
    """
    sites-conformes replaces Wagtail's image model with its CustomImage model (same ids).

    Wagtail caches renditions under keys made of the image id (without its model) and, when found,
    assigns the current image to them: the renditions cached for wagtailimages.Image then fail with
    'Cannot assign "<CustomImage: ...>": "Rendition.image" must be a "Image" instance.'
    Delete them (only them: the cache may be shared), new ones are created on the next display.
    """
    try:
        cache = caches["renditions"]  # same backend as AbstractRendition.cache_backend
    except InvalidCacheBackendError:
        cache = caches[DEFAULT_CACHE_ALIAS]

    pattern = cache.make_key("wagtail-rendition-")
    backend = cache.__class__.__name__

    if backend == "RedisCache":
        client = cache._cache.get_client(write=True)
        keys = list(client.scan_iter(match=f"{pattern}*"))
        if keys:
            client.delete(*keys)
    elif backend == "DatabaseCache":
        connection = schema_editor.connection
        if cache._table in connection.introspection.table_names():
            table = connection.ops.quote_name(cache._table)
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {table} WHERE cache_key LIKE %s", [f"{pattern}%"])
    else:
        # local memory, file or dummy cache: nothing shared, clear it all
        cache.clear()


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0002_add_paragraphs"),
        ("sites_conformes_customimages", "0002_copy_wagtail_images"),
    ]

    operations = [
        migrations.RunPython(clear_cached_renditions, migrations.RunPython.noop, elidable=True),
    ]
