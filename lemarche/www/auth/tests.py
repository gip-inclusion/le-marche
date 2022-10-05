from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.users.models import User


SIAE = {
    # "id_kind": 0  # required
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
    # "id_kind": 1  # required
    "first_name": "Prenom",
    "last_name": "Nom",
    "phone": "012345678",
    "company_name": "Ma boite",
    "position": "Role important",
    "email": "buyer@example.com",
    "password1": "Erls92#32",
    "password2": "Erls92#32",
    # "id_accept_rgpd"  # required
    # "id_accept_survey"  # not required
}

PARTNER = {
    # "id_kind": 2  # required
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
    # "id_kind": 2  # required
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

    def test_siae_submits_signup_form_success(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_0").click()
        for key in SIAE:
            driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(SIAE[key])
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # user should be automatically logged in
        header = driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" in header.text)
        self.assertTrue("Connexion" not in header.text)
        # should redirect to user dashboard
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('dashboard:home')}")
        # message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div.messages")
        self.assertTrue("Vous pouvez maintenant ajouter votre structure" in messages.text)

    def test_siae_submits_signup_form_error(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_0").click()
        for key in SIAE:
            if key not in ["last_name"]:
                driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(SIAE[key])
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should not submit form (last_name field is required)
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_buyer_submits_signup_form_success(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_1").click()
        for key in BUYER:
            driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # user should be automatically logged in
        header = driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" in header.text)
        self.assertTrue("Connexion" not in header.text)
        # should redirect to home
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('pages:home')}")
        # message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div.messages")
        self.assertTrue("Inscription validée" in messages.text)

    def test_buyer_submits_signup_form_error(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_1").click()
        for key in BUYER:
            if key not in ["position"]:
                driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(BUYER[key])
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should not submit form (position field is required)
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_partner_submits_signup_form_success(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_2").click()
        for key in PARTNER:
            driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(PARTNER[key])
        driver.find_element(By.XPATH, "//select[@id='id_partner_kind']/option[text()='Réseaux IAE']").click()
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # user should be automatically logged in
        header = driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" in header.text)
        self.assertTrue("Connexion" not in header.text)
        # should redirect to home
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('pages:home')}")
        # message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div.messages")
        self.assertTrue("Inscription validée" in messages.text)

    def test_partner_submits_signup_form_error(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_2").click()
        for key in PARTNER:
            if key not in ["company_name"]:
                driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(PARTNER[key])
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should not submit form (company_name field is required)
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_user_submits_signup_form_with_next_param_success_and_redirect(self):
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:signup')}?next=/prestataires/?kind=ESAT")

        driver.find_element(By.CSS_SELECTOR, "input#id_kind_2").click()
        for key in PARTNER:
            driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(PARTNER[key])
        driver.find_element(By.XPATH, "//select[@id='id_partner_kind']/option[text()='Réseaux IAE']").click()
        driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd").click()

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should create User
        self.assertEqual(User.objects.count(), self.user_count + 1)
        # user should be automatically logged in
        header = driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" in header.text)
        self.assertTrue("Connexion" not in header.text)
        # should redirect to next url
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('siae:search_results')}?kind=ESAT")
        # message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div.messages")
        self.assertTrue("Inscription validée" in messages.text)

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

        # should redirect SIAE to profil
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('dashboard:home')}")

    def test_non_siae_user_can_sign_in_and_is_redirected_to_home(self):
        user_buyer = UserFactory(email="buyer5@example.com", kind=User.KIND_BUYER)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_buyer.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button").click()

        # should redirect BUYER to home
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('pages:home')}")

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
