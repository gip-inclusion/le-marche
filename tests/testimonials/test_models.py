import datetime

from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial
from tests.siaes.factories import SiaeFactory
from tests.testimonials.factories import SiaeTestimonialFactory


class SiaeTestimonialModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()

    def test_str(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, client_email="test@example.com")
        self.assertIn("test@example.com", str(testimonial))
        self.assertIn(self.siae.name, str(testimonial))

    def test_unique_together_siae_client_email(self):
        SiaeTestimonialFactory(siae=self.siae, client_email="doublon@example.com")
        with self.assertRaises(Exception):
            SiaeTestimonialFactory(siae=self.siae, client_email="doublon@example.com")

    def test_token_is_valid_when_not_expired(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae)
        self.assertTrue(testimonial.is_token_valid)

    def test_token_is_invalid_when_expired(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, expired=True)
        self.assertFalse(testimonial.is_token_valid)

    def test_token_is_invalid_when_no_expiry(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, token_expires_at=None)
        self.assertFalse(testimonial.is_token_valid)

    def test_author_display_name_with_first_and_last(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, author_first_name="Marie", author_last_name="Dupont")
        self.assertEqual(testimonial.author_display_name, "Marie Dupont")

    def test_author_display_name_with_first_only(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, author_first_name="Marie", author_last_name="")
        self.assertEqual(testimonial.author_display_name, "Marie")

    def test_author_display_name_empty(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, author_first_name="", author_last_name="")
        self.assertEqual(testimonial.author_display_name, "")

    @freeze_time("2026-05-01 10:00:00")
    def test_publish_updates_status_and_published_at(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, submitted=True)
        testimonial.publish()
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_PUBLISHED)
        self.assertIsNotNone(testimonial.published_at)

    def test_reject_updates_status(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, submitted=True)
        testimonial.reject()
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_REJECTED)


class SiaeTestimonialQuerySetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.siae2 = SiaeFactory()
        cls.sent = SiaeTestimonialFactory(siae=cls.siae)
        cls.submitted = SiaeTestimonialFactory(siae=cls.siae, submitted=True)
        cls.published = SiaeTestimonialFactory(siae=cls.siae, published=True)

    def test_is_sent(self):
        qs = SiaeTestimonial.objects.is_sent()
        self.assertIn(self.sent, qs)
        self.assertNotIn(self.submitted, qs)

    def test_is_submitted(self):
        qs = SiaeTestimonial.objects.is_submitted()
        self.assertIn(self.submitted, qs)
        self.assertNotIn(self.sent, qs)

    def test_is_published(self):
        qs = SiaeTestimonial.objects.is_published()
        self.assertIn(self.published, qs)
        self.assertNotIn(self.sent, qs)

    def test_filter_by_siae(self):
        other = SiaeTestimonialFactory(siae=self.siae2)
        qs = SiaeTestimonial.objects.filter_by_siae(self.siae)
        self.assertIn(self.sent, qs)
        self.assertNotIn(other, qs)

    def test_sent_this_week(self):
        qs = SiaeTestimonial.objects.sent_this_week(self.siae)
        self.assertIn(self.sent, qs)

    def test_sent_this_week_excludes_old(self):
        old = SiaeTestimonialFactory(
            siae=self.siae,
            sent_at=timezone.now() - datetime.timedelta(days=8),
        )
        qs = SiaeTestimonial.objects.sent_this_week(self.siae)
        self.assertNotIn(old, qs)
