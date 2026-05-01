from django.test import TestCase
from django.urls import reverse

from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial
from tests.siaes.factories import SiaeFactory
from tests.testimonials.factories import SiaeTestimonialFactory
from tests.users.factories import UserFactory


class TestimonialSubmitViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.testimonial = SiaeTestimonialFactory(siae=cls.siae)
        cls.url = reverse("testimonials:submit", kwargs={"token": cls.testimonial.token})

    def test_get_valid_token_displays_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.siae.name)

    def test_get_expired_token_redirects(self):
        expired = SiaeTestimonialFactory(siae=self.siae, expired=True)
        url = reverse("testimonials:submit", kwargs={"token": expired.token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_get_already_submitted_redirects_to_confirm(self):
        submitted = SiaeTestimonialFactory(siae=self.siae, submitted=True)
        url = reverse("testimonials:submit", kwargs={"token": submitted.token})
        response = self.client.get(url)
        self.assertRedirects(response, reverse("testimonials:confirm", kwargs={"token": submitted.token}))

    def test_post_valid_submits_testimonial(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae)
        url = reverse("testimonials:submit", kwargs={"token": testimonial.token})
        data = {
            "content": "Très bon partenariat, équipe réactive.",
            "author_first_name": "Pierre",
            "author_last_name": "Martin",
            "author_organization": "Entreprise XY",
            "honeypot": "",
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse("testimonials:confirm", kwargs={"token": testimonial.token}))
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_SUBMITTED)
        self.assertEqual(testimonial.content, "Très bon partenariat, équipe réactive.")
        self.assertIsNotNone(testimonial.submitted_at)

    def test_post_honeypot_filled_rejects(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae)
        url = reverse("testimonials:submit", kwargs={"token": testimonial.token})
        data = {
            "content": "Spam",
            "author_first_name": "Bot",
            "honeypot": "je suis un bot",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_SENT)

    def test_post_links_buyer_user_if_email_matches(self):
        buyer = UserFactory(email="buyer@example.com", company_name="Buyer Corp")
        testimonial = SiaeTestimonialFactory(siae=self.siae, client_email="buyer@example.com")
        url = reverse("testimonials:submit", kwargs={"token": testimonial.token})
        data = {
            "content": "Super partenariat.",
            "author_first_name": "Buyer",
            "honeypot": "",
        }
        self.client.post(url, data)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.buyer_user, buyer)
        self.assertEqual(testimonial.author_organization, "Buyer Corp")

    def test_post_invalid_missing_content(self):
        testimonial = SiaeTestimonialFactory(siae=self.siae)
        url = reverse("testimonials:submit", kwargs={"token": testimonial.token})
        data = {"content": "", "author_first_name": "Pierre", "honeypot": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        testimonial.refresh_from_db()
        self.assertEqual(testimonial.status, testimonial_constants.STATUS_SENT)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()


class TestimonialConfirmViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.siae = SiaeFactory()
        cls.testimonial = SiaeTestimonialFactory(siae=cls.siae, submitted=True)
        cls.url = reverse("testimonials:confirm", kwargs={"token": cls.testimonial.token})

    def test_confirm_page_displays(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merci")
