from django.conf import settings


def whitelist_recipient_list(recipient_list):
    """
    In non-prod environments, this method will filter out non-beta.gouv.fr emails.
    """
    if settings.BITOUBI_ENV == "prod":
        return recipient_list
    else:
        EMAIL_WHITELIST_ENDSWITH = "beta.gouv.fr"
        return [email for email in recipient_list if (email and email.endswith(EMAIL_WHITELIST_ENDSWITH))]
