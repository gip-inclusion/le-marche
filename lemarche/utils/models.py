def get_object_by_id_or_none(classmodel, id: int | str | None):
    """
    https://stackoverflow.com/a/20674112/4293684
    """
    if id:
        try:
            return classmodel.objects.get(id=int(id))
        except classmodel.DoesNotExist:
            pass
    return None
