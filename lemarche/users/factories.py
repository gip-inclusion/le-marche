import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from lemarche.users.models import User


DEFAULT_PASSWORD = "P4ssw0rd!*"


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Sequence("first_name{0}".format)
    last_name = factory.Sequence("last_name{0}".format)
    email = factory.Sequence("email{0}@example.com".format)
    password = factory.PostGenerationMethodCall("set_password", DEFAULT_PASSWORD)
    phone = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    kind = User.KIND_SIAE
