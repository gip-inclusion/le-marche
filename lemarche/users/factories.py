import functools

import factory
from django.contrib.auth.hashers import make_password
from factory.django import DjangoModelFactory

from lemarche.users.models import User


DEFAULT_PASSWORD = "P4ssw0rd!*"


@functools.cache
def default_password():
    return make_password(DEFAULT_PASSWORD)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True  # Prevents unnecessary save

    first_name = factory.Sequence("first_name{0}".format)
    last_name = factory.Sequence("last_name{0}".format)
    email = factory.Sequence("email{0}@example.com".format)
    password = factory.LazyFunction(default_password)
    phone = "0666666666"
    kind = User.KIND_SIAE

    @factory.post_generation
    def siaes(self, create, extracted, **kwargs):
        if extracted:
            # Add the iterable of groups using bulk addition
            self.siaes.add(*extracted)
