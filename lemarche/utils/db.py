from django.db import transaction


@transaction.atomic
def secure_delete(queryset, allowed_models):
    _, deleted = queryset.delete()
    if forbidden_models := set(deleted.keys()) - set(allowed_models):
        raise Exception(f"Forbidden models deleted: {sorted(forbidden_models)}")
    return deleted
