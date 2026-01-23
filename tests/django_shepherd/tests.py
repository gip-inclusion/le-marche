from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse

from lemarche.django_shepherd.context_processor import expose_guide_context
from lemarche.django_shepherd.models import UserGuide


class GuideContextTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.url_with_param = "http://localhost:8000/prestataires/truc/?blalb=something"
        self.already_seen_user = get_user_model().objects.create_user(email="fake@email.com", password="1234")
        self.guide = UserGuide.objects.create(name="guide_1", url=self.url_with_param)
        self.guide.guided_users.add(self.already_seen_user)

    def test_anonymous_user(self):
        request = self.request_factory.get(self.url_with_param)
        request.user = AnonymousUser()
        context = expose_guide_context(request)
        self.assertEqual(
            context,
            {
                "DISPLAY_GUIDE_FLAG": False,
                "DISPLAY_GUIDE_VIEWED_URL": None,
                "DISPLAY_GUIDE_PAYLOAD": None,
            },
        )

    def test_logged_user(self):
        user = get_user_model()()
        request = self.request_factory.get(self.url_with_param)
        request.user = user

        context = expose_guide_context(request)
        self.assertEqual(
            context,
            {
                "DISPLAY_GUIDE_FLAG": True,
                "DISPLAY_GUIDE_VIEWED_URL": reverse("django_shepherd:guide_viewed_view", kwargs={"pk": self.guide.pk}),
                "DISPLAY_GUIDE_PAYLOAD": {"steps": []},
            },
        )

    def test_already_seen_user(self):
        request = self.request_factory.get(self.url_with_param)
        request.user = self.already_seen_user

        context = expose_guide_context(request)
        self.assertEqual(
            context,
            {
                "DISPLAY_GUIDE_FLAG": False,
                "DISPLAY_GUIDE_VIEWED_URL": None,
                "DISPLAY_GUIDE_PAYLOAD": None,
            },
        )


class StepViewed(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email="fake@email.com", password="1234")
        self.url_with_param = "http://localhost:8000/prestataires/truc/?blalb=something"
        self.guide = UserGuide.objects.create(name="guide_1", url=self.url_with_param)

    def test_test_viewed(self):
        """Check that the view is correctly adding the logged user to the list of user that has seen the guide"""
        self.assertEqual(self.guide.guided_users.count(), 0)
        self.client.force_login(self.user)
        response = self.client.get(reverse("django_shepherd:guide_viewed_view", kwargs={"pk": self.guide.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.guide.guided_users.count(), 1)

    def test_viewed_anonymous(self):
        self.assertEqual(self.guide.guided_users.count(), 0)
        response = self.client.get(reverse("django_shepherd:guide_viewed_view", kwargs={"pk": self.guide.pk}))
        self.assertEqual(response.status_code, 302)  # redirected to login page
        self.assertEqual(self.guide.guided_users.count(), 0)
