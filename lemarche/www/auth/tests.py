from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.select import Select

from lemarche.cms.snippets import Paragraph
from lemarche.users.factories import DEFAULT_PASSWORD, UserFactory
from lemarche.users.models import User


def scroll_to_and_click_element(driver, element, click=True):
    """
    Helper to avoid some errors with selenium
    - selenium.common.exceptions.ElementNotInteractableException
    - selenium.common.exceptions.ElementClickInterceptedException
    """
    # click instead with javascript
    driver.execute_script("arguments[0].scrollIntoView();", element)
    # small pause
    if click:
        try:
            element.click()
        except:  # noqa # selenium.common.exceptions.ElementClickInterceptedException
            driver.execute_script("arguments[0].click();", element)


def element_select_option(driver, element, option=""):
    field_select = Select(element)
    scroll_to_and_click_element(driver, element, click=False)
    field_select.select_by_visible_text(option)


class SignupFormTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # selenium browser
        options = Options()
        options.add_argument("-headless")
        cls.driver = webdriver.Firefox(options=options)
        cls.driver.implicitly_wait(1)

    def setUp(self):
        EXAMPLE_PASSWORD = "c*[gkp`0="
        # Static server tests cases erases data from migrations
        Paragraph.objects.get_or_create(
            slug="rdv-signup",
            defaults={"title": "Prise de rendez vous"},
        )

        self.SIAE = {
            "id_kind": 0,  # required
            "first_name": "Prenom",
            "last_name": "Nom",
            "phone": "+33123456789",  # not required
            "email": "siae@example.com",
            "password1": EXAMPLE_PASSWORD,
            "password2": EXAMPLE_PASSWORD,
        }

        self.BUYER = {
            "id_kind": 1,  # required
            "first_name": "Prenom",
            "last_name": "Nom",
            "phone": "0123456789",
            "company_name": "Ma boite",
            "position": "Role important",
            "email": "buyer@example.com",
            "password1": EXAMPLE_PASSWORD,
            "password2": EXAMPLE_PASSWORD,
        }

        self.PARTNER = {
            "id_kind": 2,  # required
            "first_name": "Prenom",
            "last_name": "Nom",
            "phone": "01 23 45 67 89",  # not required
            "company_name": "Ma boite",
            "email": "partner@example.com",
            "password1": EXAMPLE_PASSWORD,
            "password2": EXAMPLE_PASSWORD,
        }

        self.PARTNER_2 = {
            "id_kind": 2,  # required
            "first_name": "Prenom",
            "last_name": "Nom",
            "phone": "+33123456789",  # not required
            "company_name": "Ma boite",
            "email": "partner2@example.com",
            "password1": EXAMPLE_PASSWORD,
            "password2": EXAMPLE_PASSWORD,
        }

        self.INDIVIDUAL = {
            "id_kind": 3,
            "first_name": "Prenom",
            "last_name": "Nom",
            "email": "individual@example.com",
            "password1": EXAMPLE_PASSWORD,
            "password2": EXAMPLE_PASSWORD,
        }

    def _complete_form(self, user_profile: dict, signup_url=reverse("auth:signup"), with_submit=True):
        """the function allows you to go to the "signup" page and complete the user profile.

        Args:
            user_profile (dict): Dict wich contains the users information for form.
                                ex : { "id_kind": 0, "id_of_field": "value"}
            with_submit (bool, optional): Submit the form if it's True. Defaults to True.
        """
        self.driver.get(f"{self.live_server_url}{signup_url}")

        # manage tarteaucitron popup
        try:
            self.driver.find_element(By.CSS_SELECTOR, "button#tarteaucitronAllDenied2").click()
        except:  # noqa # selenium.common.exceptions.NoSuchElementException:
            pass

        user_kind = user_profile.pop("id_kind")
        self.driver.find_element(By.CSS_SELECTOR, f"label[for='id_kind_{user_kind}']").click()
        for key in user_profile:
            self.driver.find_element(By.CSS_SELECTOR, f"input#id_{key}").send_keys(user_profile[key])
        accept_rgpd_element = self.driver.find_element(By.CSS_SELECTOR, "input#id_accept_rgpd")
        scroll_to_and_click_element(self.driver, accept_rgpd_element)

        if with_submit:
            submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
            scroll_to_and_click_element(self.driver, submit_element)

    def _assert_signup_success(self, redirect_url: str, user_kind=None) -> list:
        """Assert the success signup and returns the success messages

        Args:
            redirect_url (str): redirect url after signup

        Returns:
            list: list of success messages
        """
        # should create User
        self.assertEqual(User.objects.count(), 1)
        # user should be automatically logged in
        header = self.driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Connexion" not in header.text)

        menu_button = self.driver.find_element(By.ID, "my-account")
        menu_button.click()

        notifications_link = self.driver.find_elements(By.LINK_TEXT, "Notifications")
        if user_kind in [User.KIND_SIAE, User.KIND_BUYER]:
            self.assertTrue(len(notifications_link) > 0)
        else:
            # find_elements returns an empty list if no element found and doesn't raise an error
            self.assertFalse(notifications_link)

        # should redirect to redirect_url
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{redirect_url}")
        # message should be displayed
        messages = self.driver.find_element(By.CSS_SELECTOR, "div.fr-alert--success")
        self.assertTrue("Inscription validée" in messages.text)
        return messages

    def test_siae_submits_signup_form_success(self):
        self._complete_form(user_profile=self.SIAE, with_submit=True)

        # should redirect SIAE to dashboard
        self._assert_signup_success(redirect_url=reverse("auth:booking-meeting-view"), user_kind=User.KIND_SIAE)

    def test_siae_submits_signup_form_error(self):
        user_profile = self.SIAE
        del user_profile["last_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (last_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_siae_submits_signup_form_email_already_exists(self):
        UserFactory(email=self.SIAE["email"], kind=User.KIND_SIAE)

        user_profile = self.SIAE
        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (email field already used)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

        alerts = self.driver.find_element(By.CSS_SELECTOR, "form")
        self.assertTrue("Cette adresse e-mail est déjà utilisée." in alerts.text)

    def test_buyer_submits_signup_form_success(self):
        self._complete_form(user_profile=self.BUYER, with_submit=False)

        buyer_kind_detail_select_element = self.driver.find_element(By.CSS_SELECTOR, "select#id_buyer_kind_detail")
        element_select_option(self.driver, buyer_kind_detail_select_element, "Grand groupe (+5000 salariés)")

        submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, submit_element)

        # should redirect BUYER to search
        self._assert_signup_success(redirect_url=reverse("auth:booking-meeting-view"), user_kind=User.KIND_BUYER)

    def test_buyer_submits_signup_form_success_extra_data(self):
        self._complete_form(user_profile=self.BUYER, with_submit=False)

        buyer_kind_detail_select_element = self.driver.find_element(By.CSS_SELECTOR, "select#id_buyer_kind_detail")
        element_select_option(self.driver, buyer_kind_detail_select_element, "Grand groupe (+5000 salariés)")

        nb_of_handicap = "3"
        nb_of_inclusive = "4"
        nb_of_handicap_provider_last_year_element = self.driver.find_element(
            By.CSS_SELECTOR, f"input#id_nb_of_handicap_provider_last_year_{nb_of_handicap}"
        )
        scroll_to_and_click_element(self.driver, nb_of_handicap_provider_last_year_element)
        nb_of_inclusive_provider_last_year_element = self.driver.find_element(
            By.CSS_SELECTOR, f"input#id_nb_of_inclusive_provider_last_year_{nb_of_inclusive}"
        )
        scroll_to_and_click_element(self.driver, nb_of_inclusive_provider_last_year_element)
        submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, submit_element)
        # should get created User
        user = User.objects.get(email=self.BUYER["email"])

        # assert extra_data are inserted
        self.assertEqual(user.extra_data.get("nb_of_handicap_provider_last_year"), nb_of_handicap)
        self.assertEqual(user.extra_data.get("nb_of_inclusive_provider_last_year"), nb_of_inclusive)

    def test_buyer_submits_signup_form_error(self):
        user_profile = self.BUYER
        del user_profile["position"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (position field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_partner_submits_signup_form_success(self):
        self._complete_form(user_profile=self.PARTNER, with_submit=False)
        partner_kind_option_element = self.driver.find_element(
            By.XPATH, "//select[@id='id_partner_kind']/option[text()='Réseaux IAE']"
        )
        scroll_to_and_click_element(self.driver, partner_kind_option_element)
        submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, submit_element)

        self._assert_signup_success(redirect_url=reverse("auth:booking-meeting-view"))

    def test_partner_submits_signup_form_error(self):
        user_profile = self.PARTNER
        del user_profile["company_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (company_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    # TODO: problem with this test
    # def test_individual_submits_signup_form_success(self):
    #     self._complete_form(user_profile=INDIVIDUAL, with_submit=False)

    #     # should redirect INDIVIDUAL to home
    #     self._assert_signup_success(redirect_url=reverse("wagtail_serve", args=("",)))

    def test_individual_submits_signup_form_error(self):
        user_profile = self.INDIVIDUAL
        del user_profile["last_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (last_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('auth:signup')}")

    def test_user_submits_signup_form_with_next_param_success_and_redirect(self):
        next_url = f"{reverse('siae:search_results')}?kind=ESAT"
        self._complete_form(
            user_profile=self.SIAE,
            signup_url=f"{reverse('auth:signup')}?next={next_url}",
            with_submit=False,
        )
        submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, submit_element)

        self._assert_signup_success(redirect_url=next_url, user_kind=User.KIND_SIAE)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()


class LoginFormTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument("-headless")

        # Create a Firefox profile to set the locale to French (needed for the login form)
        profile = webdriver.FirefoxProfile()
        profile.set_preference("intl.accept_languages", "fr")
        options.profile = profile

        cls.driver = webdriver.Firefox(options=options)
        cls.driver.implicitly_wait(1)

    def test_siae_user_can_sign_in_and_is_redirected_to_dashboard(self):
        user_siae = UserFactory(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_siae.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should redirect SIAE to dashboard
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('dashboard:home')}")

    def test_non_siae_user_can_sign_in_and_is_redirected_to_home(self):
        user_buyer = UserFactory(email="buyer5@example.com", kind=User.KIND_BUYER)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_buyer.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should redirect BUYER to search
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('siae:search_results')}")

    def test_user_can_sign_in_with_email_containing_capital_letters(self):
        UserFactory(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys("SIAE5@example.com")
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

    def test_user_wrong_credentials_should_see_error_message(self):
        user_siae = UserFactory(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys(user_siae.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys("password")

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should not submit form
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:login')}")
        # error message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "section.fr-input-group--error")
        self.assertTrue("Saisissez un Adresse e-mail et un mot de passe valides" in messages.text)

    def test_user_empty_credentials_should_see_password_reset_message(self):
        existing_user = UserFactory(email="existing-user@example.com", password="")
        # only way to have an empty password field
        User.objects.filter(id=existing_user.id).update(password="")
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('auth:login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_username").send_keys("existing-user@example.com")
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys("password")

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should not submit form
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('auth:login')}")
        # # new-user-without-password-login-message message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "div#new-user-without-password-login-message")
        self.assertTrue("pas encore défini de mot de passe" in messages.text)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()
