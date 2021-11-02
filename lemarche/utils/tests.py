from unittest import mock

from django.test import TestCase
from django.urls import reverse

from lemarche.utils.emails import whitelist_recipient_list


def mock_track(path, action, **kargs):
    return "track"


class TrackerTest(TestCase):
    @mock.patch("lemarche.utils.tracker.track")
    def test_tracker_is_called(self, mock_track):
        url = reverse("pages:home")
        self.client.get(url)
        self.assertEqual(mock_track.call_count, 1)

    # @mock.patch("lemarche.utils.tracker.track")
    # def test_tracker_is_called_twice_on_siae_search(self, mock_track):
    #     url = reverse("siae:search_results")
    #     self.client.get(url)
    #     self.assertEqual(mock_track.call_count, 2)

    @mock.patch("lemarche.utils.tracker.track")
    def test_tracker_is_not_called_for_request_in_ignore_list(self, mock_track):
        url = reverse("api:perimeters-list")
        self.client.get(url)
        self.assertEqual(mock_track.call_count, 0)

    @mock.patch("lemarche.utils.tracker.track")
    def test_tracker_is_not_called_for_request_from_bot(self, mock_track):
        bot_ua = "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)"
        url = reverse("pages:home")
        self.client.get(url, HTTP_USER_AGENT=bot_ua)
        self.assertEqual(mock_track.call_count, 0)


class EmailTest(TestCase):
    def should_filter_out_non_betagouv_emails_when_not_in_prod(self):
        email_list = ["test@beta.gouv.fr", "test@example.com"]
        email_list_filtered = whitelist_recipient_list(email_list)
        self.assertTrue("test@beta.gouv.fr" in email_list_filtered)
        self.assertTrue("test@example.com" not in email_list_filtered)
