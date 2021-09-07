from hashids import Hashids
from rest_framework.exceptions import APIException

from lemarche.users.models import User


# Custom Service Exceptions
class Unauthorized(APIException):
    status_code = 401
    default_detail = "Unauthorized"
    default_code = "unauthorized"


def ensure_user_permission(token):
    """
    User token functionnality is temporary, and only used
    to trace API usage and support : once a proper
    auth protocol is implemented it will be replaced
    """
    try:
        user = User.objects.get(api_key=token)
        assert user.has_perm("api.access_api")
    except (User.DoesNotExist, AssertionError):
        raise Unauthorized


hasher = Hashids(alphabet="1234567890ABCDEF", min_length=5)


def decode_hashed_pk(func):
    """
    Small decorator to dynamically decode a hashed pk
    """

    def _wrapper(*args, **kwargs):
        if "pk" in kwargs.keys():
            kwargs["pk"] = hasher.decode(kwargs["pk"])[0]
        return func(*args, **kwargs)

    return _wrapper
