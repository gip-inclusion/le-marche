from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

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
                "DISPLAY_GUIDE_PK": None,
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
                "DISPLAY_GUIDE_PK": self.guide.pk,
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
                "DISPLAY_GUIDE_PK": None,
                "DISPLAY_GUIDE_PAYLOAD": None,
            },
        )
