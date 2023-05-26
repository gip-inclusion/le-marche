from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.users.models import User


SIAE = {
    "id_kind": 0,  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",  # not required
    # "company_name": "",  # not asked here
    "email": "siae@example.com",
    "password1": "Erls92#32",
    "password2": "Erls92#32",
    # "id_accept_rgpd"  # required
}

BUYER = {
    "id_kind": 1,  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",
    "company_name": "Ma boite",
    "position": "Role important",
    "email": "buyer@example.com",
    "password1": "Erls92#32",
    "password2": "Erls92#32",
    # "nb_of_handicap_provider_2022": "3",
    # "nb_of_inclusive_provider_2022": "4",
    # "id_accept_rgpd"  # required
    # "id_accept_survey"  # not required
}

PARTNER = {
    "id_kind": 2,  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",  # not required
    "company_name": "Ma boite",
    # "partner_kind": "RESEAU_IAE",
    "email": "partner@example.com",
    "password1": "Erls92#32",
    "password2": "Erls92#32",
    # "id_accept_rgpd"  # required
    # "id_accept_survey"  # not required
}

PARTNER_2 = {
    "id_kind": 2,  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",  # not required
    "company_name": "Ma boite",
    # "partner_kind": "RESEAU_IAE",
    "email": "partner2@example.com",
    "password1": "Erls92#32",
    "password2": "Erls92#32",
    # "id_accept_rgpd"  # required
    # "id_accept_survey"  # not required
}


class SignupFormTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # selenium browser  # TODO: make it test-wide
        options = Options()
        options.headless = True
        cls.driver = webdriver.Firefox(options=options)
        cls.driver.implicitly_wait(1)
        # other init
        cls.user_count = User.objects.count()

    def _complete_form(self, user_profile: dict, signup_url=reverse("auth:signup"), with_submit=True):
        """the function allows you to go to the "signup" page and complete the user profile.

        Args:
            user_profile (dict): Dict wich contains the users information for form.
                                ex : { "id_kind": 0, "id_of_field": "value"}
            with_submit (bool, optional): Submit the form if it's True. Defaults to True.
        """
        self.driver.get(f"{self.live_server_url}{signup_url}")

        user_profile = user_profile.copy()
        user_kind = user_profile.pop("id_kind")
        self.driver.find_element(By.CSS_SELECTOR, f"input#id_kind_{user_kind}").click()
        for key in user_profile:
            self.driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(user_profile[key])
        self.driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        if with_submit:
            self.driver.find_element(By.CSS_SELECTOR, "form button").click()

    def _assert_signup_success(self, redirect_url: str) -> list:
        """Assert the success signup and returns the sucess messages

        Args:
            redirect_url (str): redirect url after signup

        Returns:
            list: list of success messages
        """
        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # user should be automatically logged in
        header = self.driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" in header.text)
        self.assertTrue("Connexion" not in header.text)
        # should redirect to redirect_url
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{redirect_url}")
        # message should be displayed
        messages = self.driver.find_element(By.CSS_SELECTOR, "div.messages")
        self.assertTrue("Inscription validée" in messages.text)
        return messages

    def test_siae_submits_signup_form_success(self):
        self._complete_form(user_profile=SIAE.copy(), with_submit=True)

        # should redirect SIAE to dashboard
        messages = self._assert_signup_success(redirect_url=reverse("dashboard:home"))

        self.assertTrue("Vous pouvez maintenant ajouter votre structure" in messages.text)

    def test_siae_submits_signup_form_error(self):
        user_profile = SIAE.copy()
        del user_profile["last_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (last_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_buyer_submits_signup_form_success(self):
        self._complete_form(user_profile=BUYER, with_submit=True)

        # should redirect BUYER to search
        self._assert_signup_success(redirect_url=reverse("siae:search_results"))

    def test_buyer_submits_signup_form_success_extra_data(self):
        self._complete_form(user_profile=BUYER, with_submit=False)
        nb_of_handicap = "3"
        nb_of_inclusive = "4"
        self.driver.find_element(By.CSS_SELECTOR, f"input#id_nb_of_handicap_provider_2022_{nb_of_handicap}").click()
        self.driver.find_element(By.CSS_SELECTOR, f"input#id_nb_of_inclusive_provider_2022_{nb_of_inclusive}").click()

        self.driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should get created User
        user = User.objects.get(email=BUYER.get("email"))

        # assert extra_data are inserted
        self.assertEqual(user.extra_data.get("nb_of_handicap_provider_2022"), nb_of_handicap)
        self.assertEqual(user.extra_data.get("nb_of_inclusive_provider_2022"), nb_of_inclusive)

    def test_buyer_submits_signup_form_error(self):
        user_profile = BUYER.copy()
        del user_profile["position"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (position field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_partner_submits_signup_form_success(self):
        self._complete_form(user_profile=PARTNER, with_submit=False)
        self.driver.find_element(By.XPATH, "//select[@id='id_partner_kind']/option[text()='Réseaux IAE']").click()
        self.driver.find_element(By.CSS_SELECTOR, "form button").click()

        self._assert_signup_success(redirect_url=reverse("wagtail_serve", args=("",)))

    def test_partner_submits_signup_form_error(self):
        user_profile = PARTNER.copy()
        del user_profile["company_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (company_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_user_submits_signup_form_with_next_param_success_and_redirect(self):
        next_url = f"{reverse('siae:search_results')}?kind=ESAT"
        self._complete_form(
            user_profile=PARTNER,
            signup_url=f"{reverse('auth:signup')}?next={next_url}",
            with_submit=False,
        )
        self.driver.find_element(By.XPATH, "//select[@id='id_partner_kind']/option[text()='Réseaux IAE']").click()

        self.driver.find_element(By.CSS_SELECTOR, "form button").click()

        self._assert_signup_success(redirect_url=next_url)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()


class LoginFormTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.headless = True
        cls.driver = webdriver.Firefox(options=options)
        cls.driver.implicitly_wait(1)

    def test_siae_user_can_sign_in_and_is_redirected_to_dashboard(self):
        user_siae = UserFactory(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_siae.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should redirect SIAE to dashboard
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('dashboard:home')}")

    def test_non_siae_user_can_sign_in_and_is_redirected_to_home(self):
        user_buyer = UserFactory(email="buyer5@example.com", kind=User.KIND_BUYER)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_buyer.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should redirect BUYER to search
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('siae:search_results')}")

    def test_user_can_sign_in_with_email_containing_capital_letters(self):
        UserFactory(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys("SIAE5@example.com")
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button").click()

    def test_user_wrong_credentials_should_see_error_message(self):
        user_siae = UserFactory(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_siae.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys("password")

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should not submit form
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:login')}")
        # post-migration message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div.alert-danger")
        self.assertTrue("aisissez un Adresse e-mail et un mot de passe valides" in messages.text)

    def test_user_empty_credentials_should_see_post_migration_message(self):
        existing_user = UserFactory(email="existing-user@example.com", password="")
        # only way to have an empty password field
        User.objects.filter(id=existing_user.id).update(password="")
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys("existing-user@example.com")
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys("password")

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should not submit form
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:login')}")
        # # post-migration message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div#post-migration-login-message")
        self.assertTrue("Le marché de l'inclusion fait peau neuve" in messages.text)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()
