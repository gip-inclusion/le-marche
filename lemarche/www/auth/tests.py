from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from lemarche.users.models import User


SIAE = {
    # "id_kind": 0  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",  # not required
    # "company_name": "",  # not asked here
    "email": "siae@example.com",
    "password1": "password",
    "password2": "password",
    # "id_accept_rgpd"  # required
}

BUYER = {
    # "id_kind": 1  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",
    "company_name": "Ma boite",
    "position": "Role important",
    "email": "buyer@example.com",
    "password1": "password",
    "password2": "password",
    # "id_accept_rgpd"  # required
    # "id_accept_survey"  # not required
}

PARTNER = {
    # "id_kind": 2  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",  # not required
    "company_name": "Ma boite",
    "email": "partner@example.com",
    "password1": "password",
    "password2": "password",
    # "id_accept_rgpd"  # required
    # "id_accept_survey"  # not required
}


class SignupFormTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_count = User.objects.count()
        # selenium browser  # TODO: make it app-wide
        opts = Options()
        opts.headless = True
        cls.driver = webdriver.Firefox(options=opts)
        cls.driver.implicitly_wait(1)

    def test_siae_submits_signup_form_success(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element_by_css_selector("input#id_kind_0").click()
        for key in SIAE:
            driver.find_element_by_css_selector(f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element_by_css_selector("input#id_accept_rgpd").click()

        driver.find_element_by_css_selector("form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # should redirect to home
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('pages:home')}")

    def test_siae_submits_signup_form_error(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element_by_css_selector("input#id_kind_0").click()
        for key in SIAE:
            if key not in ["last_name"]:
                driver.find_element_by_css_selector(f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element_by_css_selector("input#id_accept_rgpd").click()

        driver.find_element_by_css_selector("form button").click()

        # should not submit form (last_name field is required)
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_buyer_submits_signup_form_success(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element_by_css_selector("input#id_kind_1").click()
        for key in BUYER:
            driver.find_element_by_css_selector(f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element_by_css_selector("input#id_accept_rgpd").click()

        driver.find_element_by_css_selector("form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # should redirect to home
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('pages:home')}")

    def test_buyer_submits_signup_form_error(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element_by_css_selector("input#id_kind_1").click()
        for key in BUYER:
            if key not in ["position"]:
                driver.find_element_by_css_selector(f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element_by_css_selector("input#id_accept_rgpd").click()

        driver.find_element_by_css_selector("form button").click()

        # should not submit form (position field is required)
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_partner_submits_signup_form_success(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element_by_css_selector("input#id_kind_2").click()
        for key in PARTNER:
            driver.find_element_by_css_selector(f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element_by_css_selector("input#id_accept_rgpd").click()

        driver.find_element_by_css_selector("form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # should redirect to home
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('pages:home')}")

    def test_partner_submits_signup_form_error(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element_by_css_selector("input#id_kind_2").click()
        for key in PARTNER:
            if key not in ["company_name"]:
                driver.find_element_by_css_selector(f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element_by_css_selector("input#id_accept_rgpd").click()

        driver.find_element_by_css_selector("form button").click()

        # should not submit form (company_name field is required)
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()
