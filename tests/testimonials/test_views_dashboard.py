from django.test import TestCase
from django.urls import reverse

from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial
from tests.siaes.factories import SiaeFactory
from tests.testimonials.factories import SiaeTestimonialFactory
from tests.users.factories import UserFactory


class SiaeTestimonialListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.user = UserFactory()
        cls.siae.users.add(cls.user)
        cls.url = reverse("dashboard_siaes:siae_testimonial_list", kwargs={"slug": cls.siae.slug})

    def test_anonymous_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_member_can_access(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_member_redirected(self):
        other_user = UserFactory()
        self.client.force_login(other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_displays_testimonials(self):
        SiaeTestimonialFactory(siae=self.siae, submitted=True)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertContains(response, "En attente de validation")


class SiaeTestimonialRequestViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.user = UserFactory(first_name="Alice", last_name="Dupont")
        cls.siae.users.add(cls.user)
        cls.url = reverse("dashboard_siaes:siae_testimonial_request", kwargs={"slug": cls.siae.slug})

    def test_get_form_displays(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_post_creates_testimonial(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"client_email": "new@example.com", "custom_message": ""})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SiaeTestimonial.objects.filter(siae=self.siae, client_email="new@example.com").exists())

    def test_post_duplicate_email_redirects_with_warning(self):
        SiaeTestimonialFactory(siae=self.siae, client_email="existing@example.com")
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"client_email": "existing@example.com", "custom_message": ""})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(SiaeTestimonial.objects.filter(siae=self.siae, client_email="existing@example.com").count(), 1)

    def test_post_anti_spam_max_per_week(self):
        for i in range(testimonial_constants.MAX_PER_WEEK):
            SiaeTestimonialFactory(siae=self.siae, client_email=f"spam{i}@example.com")
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"client_email": "new@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SiaeTestimonial.objects.filter(siae=self.siae, client_email="new@example.com").exists())


class SiaeTestimonialPublishViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.user = UserFactory()
        cls.siae.users.add(cls.user)

    def test_publish_submitted_testimonial(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, submitted=True)
        self.client.force_login(self.user)
        url = reverse("dashboard_siaes:siae_testimonial_publish", kwargs={"slug": self.siae.slug, "pk": testimonial.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_PUBLISHED)

    def test_cannot_publish_beyond_max(self):
        for _ in range(testimonial_constants.MAX_PUBLISHED):
            SiaeTestimonialFactory(siae=self.siae, published=True)
        extra = SiaeTestimonialFactory(siae=self.siae, submitted=True)
        self.client.force_login(self.user)
        url = reverse("dashboard_siaes:siae_testimonial_publish", kwargs={"slug": self.siae.slug, "pk": extra.pk})
        self.client.post(url)
        extra.refresh_from_db()
        self.assertEqual(extra.status, testimonial_constants.STATUS_SUBMITTED)

    def test_cannot_publish_sent_testimonial(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae)
        self.client.force_login(self.user)
        url = reverse("dashboard_siaes:siae_testimonial_publish", kwargs={"slug": self.siae.slug, "pk": testimonial.pk})
        self.client.post(url)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_SENT)


class SiaeTestimonialRejectViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.user = UserFactory()
        cls.siae.users.add(cls.user)

    def test_reject_submitted_testimonial(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae, submitted=True)
        self.client.force_login(self.user)
        url = reverse("dashboard_siaes:siae_testimonial_reject", kwargs={"slug": self.siae.slug, "pk": testimonial.pk})
        self.client.post(url)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_REJECTED)
