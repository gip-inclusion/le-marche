import factory
from factory.django import DjangoModelFactory

from blog.models import User
from lemarche.stats.models import StatsUser


class StatsUserFactory(DjangoModelFactory):
    class Meta:
        model = StatsUser

    id = factory.Sequence(lambda n: n)
    email = factory.Sequence("email{0}@example.com".format)
    first_name = factory.Sequence("first_name{0}".format)
    last_name = factory.Sequence("last_name{0}".format)
    kind = User.KIND_SIAE
    phone = phone = "0666666666"
    company_name = factory.Sequence("Some Company N°:{0}".format)
    anonymized_at = None
