from rest_framework.exceptions import APIException

from lemarche.users.models import User


# Custom Service Exceptions
class Unauthorized(APIException):
    status_code = 401
    default_detail = "Unauthorized"
    default_code = "unauthorized"


def check_user_token(token):
    """
    User token functionnality is temporary, and only used
    to trace API usage and support : once a proper
    auth protocol is implemented it will be replaced
    """
    try:
        return User.objects.get(api_key=token)
    except (User.DoesNotExist, AssertionError):
        raise Unauthorized
