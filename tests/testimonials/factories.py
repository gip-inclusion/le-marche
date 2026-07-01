import datetime

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial
from tests.siaes.factories import SiaeFactory


class SiaeTestimonialFactory(DjangoModelFactory):
    siae = factory.SubFactory(SiaeFactory)
    client_email = factory.Sequence(lambda n: f"client{n}@example.com")
    custom_message = ""
    status = testimonial_constants.STATUS_SENT
    sent_at = factory.LazyFunction(timezone.now)
    token_expires_at = factory.LazyFunction(
        lambda: timezone.now() + datetime.timedelta(days=testimonial_constants.TOKEN_EXPIRY_DAYS)
    )
    content = ""
    author_first_name = ""
    author_last_name = ""
    author_organization = ""

    class Meta:
        model = SiaeTestimonial

    class Params:
        submitted = factory.Trait(
            status=testimonial_constants.STATUS_SUBMITTED,
            content="Excellent travail, je recommande.",
            author_first_name="Marie",
            author_last_name="Dupont",
            author_organization="Acheteur SA",
            submitted_at=factory.LazyFunction(timezone.now),
        )
        published = factory.Trait(
            status=testimonial_constants.STATUS_PUBLISHED,
            content="Excellent travail, je recommande.",
            author_first_name="Marie",
            author_last_name="Dupont",
            author_organization="Acheteur SA",
            submitted_at=factory.LazyFunction(timezone.now),
            published_at=factory.LazyFunction(timezone.now),
        )
        expired = factory.Trait(
            token_expires_at=factory.LazyFunction(
                lambda: timezone.now() - datetime.timedelta(days=1)
            ),
        )
