import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from blog.models import User
from lemarche.siaes import constants as siae_constants
from lemarche.stats.models import StatsUser, Tracker
from lemarche.users import constants as user_constants


class TrackerFactory(DjangoModelFactory):
    class Meta:
        model = Tracker

    version = 1
    date_created = timezone.now()
    env = "test"
    source = "tracker"

    data = {}

    user_id = factory.Sequence(lambda n: n)
    user_kind = user_constants.KIND_PARTNER
    isadmin = False

    siae_id = factory.Sequence(lambda n: n)
    siae_kind = siae_constants.KIND_GEIQ
    siae_contact_email = factory.Sequence("email{0}@example.com".format)


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
