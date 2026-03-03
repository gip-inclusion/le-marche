import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from lemarche.siaes import constants as siae_constants
from lemarche.stats.models import Tracker
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
