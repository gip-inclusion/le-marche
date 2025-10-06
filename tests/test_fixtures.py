from django.test import TestCase


class FixturesTest(TestCase):
    fixtures = [
        "lemarche/fixtures/django/0a_networks.json",
        "lemarche/fixtures/django/0b_sectorgroups.json",
        "lemarche/fixtures/django/0c_sectors.json",
        "lemarche/fixtures/django/0d_labels.json",
        "lemarche/fixtures/django/0e_companies.json",
        "lemarche/fixtures/django/01_siaegroups.json",
        "lemarche/fixtures/django/01_siaegroup_sectors.json",
        "lemarche/fixtures/django/01_siaes.json",
        "lemarche/fixtures/django/02_users.json",
        "lemarche/fixtures/django/03_siae_users.json",
        "lemarche/fixtures/django/04_siae_siaegroups.json",
        "lemarche/fixtures/django/08_siae_networks.json",
        "lemarche/fixtures/django/09_siaeclientreferences.json",
        "lemarche/fixtures/django/09_siaelabels_old.json",
        "lemarche/fixtures/django/09_siaeoffers.json",
        "lemarche/fixtures/django/10_tenders.json",
        "lemarche/fixtures/django/11_tender_questions.json",
        "lemarche/fixtures/django/11_tender_sectors.json",
        "lemarche/fixtures/django/11_tender_siaes.json",
        "lemarche/fixtures/django/20_cms.json",
        "lemarche/fixtures/django/21_suggested_questions.json",
        "lemarche/fixtures/django/22_tender_instructions.json",
        "lemarche/fixtures/django/23_purchases.json",
    ]

    def test_flat_fixtures_load_successfully(self):
        # if this test passes, the fixtures have loaded successfully
        pass
