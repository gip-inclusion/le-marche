def get_info_from_email_prefix(email_prefix: str) -> list:
    """
    Extract info from email_prefix
    version 0 format: uuid_b, uuid_s (long uuid)
    vesion 1 format: prenom_nom_uuid (short uuid)

    Args:
        email_prefix (str): _description_

    Returns:
        [VERSION, UUID, KIND_SENDER]
    """
    email_prefix_infos = email_prefix.split("_")
    # specificity of version 0: only 1 char at the end
    if len(email_prefix_infos[-1]) == 1:
        version = 0
        uuid = email_prefix_infos[0]
        kind_sender = email_prefix_infos[1]
    else:  # version 1
        version = 1
        uuid = email_prefix_infos[-1]
        kind_sender = None  # not useful
    return version, uuid, kind_sender
