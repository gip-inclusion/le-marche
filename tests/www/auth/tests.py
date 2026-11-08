import re
from unittest.mock import patch

from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from django.contrib.messages import get_messages
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from freezegun import freeze_time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.select import Select

from lemarche.cms.snippets import Paragraph
from lemarche.users.models import User
from lemarche.www.auth.forms import CustomSignupForm
from tests.siaes.factories import SiaeFactory
from tests.users.factories import DEFAULT_PASSWORD, UserFactory


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


def create_user_with_verified_email(**kwargs):
    """Email verification is mandatory to log in: create the user with a verified address."""
    user = UserFactory(**kwargs)
    EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    return user


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
        options.set_preference("intl.accept_languages", "fr")
        cls.driver = webdriver.Firefox(options=options)
        cls.driver.implicitly_wait(1)

    def setUp(self):
        EXAMPLE_PASSWORD = "c*[gkp`0="
        # Static server tests cases erases data from migrations
        Paragraph.objects.get_or_create(
            slug="rdv-signup",
            defaults={"title": "Prise de rendez vous"},
        )
        Paragraph.objects.get_or_create(
            slug="rdv-contact",
            defaults={"title": "Numéro tel"},
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

    def _complete_form(self, user_profile: dict, signup_url=reverse("account_signup"), with_submit=True):
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

        Email verification is mandatory: the user is created but not logged in, and is asked to confirm
        the address. Following the confirmation link (in the same browser) logs the user in.

        Args:
            redirect_url (str): redirect url after signup, once the address is confirmed

        Returns:
            list: list of success messages
        """
        # should create User, without logging in
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(
            self.driver.current_url, f"{self.live_server_url}{reverse('account_email_verification_sent')}"
        )
        header = self.driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" not in header.text)

        # confirm the address with the link sent by email
        confirmation_emails = [email for email in mail.outbox if user.email in email.to]
        self.assertEqual(len(confirmation_emails), 1)
        confirmation_url = re.search(r"https?://\S+/confirm-email/\S+/", confirmation_emails[0].body).group(0)
        self.driver.get(confirmation_url)
        confirm_button = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, confirm_button)

        # user should now be logged in
        header = self.driver.find_element(By.CSS_SELECTOR, "header#header")
        self.assertTrue("Mon espace" in header.text)

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
        if user_kind != User.KIND_BUYER:
            message_list = [
                message.text for message in self.driver.find_elements(By.CSS_SELECTOR, "div.fr-alert--success")
            ]
            return message_list

    def test_siae_submits_signup_form_error(self):
        user_profile = self.SIAE
        del user_profile["last_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (last_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('account_signup')}")

    def test_siae_submits_signup_form_email_already_exists(self):
        """Same response as for a new address (no user enumeration): an email is sent to the existing account"""
        UserFactory(email=self.SIAE["email"], kind=User.KIND_SIAE)

        user_profile = self.SIAE
        self._complete_form(user_profile=user_profile, with_submit=True)

        self.assertEqual(
            self.driver.current_url, f"{self.live_server_url}{reverse('account_email_verification_sent')}"
        )
        self.assertNotIn("déjà utilisée", self.driver.page_source)
        # no new account
        self.assertEqual(User.objects.count(), 1)
        emails = [email for email in mail.outbox if self.SIAE["email"] in email.to]
        self.assertEqual([email.subject for email in emails], ["Votre compte sur le Marché de l'inclusion"])

    @freeze_time("2025-03-05")
    @patch("lemarche.utils.apis.api_brevo.BrevoContactsApiClient")
    def test_buyer_submits_signup_form_success(self, mock_brevo_contacts_client):
        mock_client_instance = mock_brevo_contacts_client.return_value
        self._complete_form(user_profile=self.BUYER, with_submit=False)

        buyer_kind_detail_select_element = self.driver.find_element(By.CSS_SELECTOR, "select#id_buyer_kind_detail")
        element_select_option(self.driver, buyer_kind_detail_select_element, "Grand groupe (+5000 salariés)")

        submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, submit_element)

        # should redirect BUYER to search
        self._assert_signup_success(
            redirect_url=reverse("siae:search_results") + "?show_invite_colleagues_modal=true",
            user_kind=User.KIND_BUYER,
        )
        # assert Brevo contact creation
        mock_client_instance.create_contact.assert_called_once()

    def test_buyer_submits_signup_form_error(self):
        user_profile = self.BUYER
        del user_profile["position"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (position field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('account_signup')}")

    # TODO: problem with this test - LiveServer erases migrations, "wagtail_serve" is a 404 (no header#header)
    # def test_partner_submits_signup_form_success(self):
    #     self._complete_form(user_profile=self.PARTNER, with_submit=False)
    #     partner_kind_option_element = self.driver.find_element(
    #         By.XPATH, "//select[@id='id_partner_kind']/option[text()='Réseaux IAE']"
    #     )
    #     scroll_to_and_click_element(self.driver, partner_kind_option_element)
    #     submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
    #     scroll_to_and_click_element(self.driver, submit_element)
    #     messages = self._assert_signup_success(redirect_url=reverse("wagtail_serve", args=("",)))
    #     self.assertIn("Connexion avec partner@example.com réussie.", messages)

    def test_partner_submits_signup_form_error(self):
        user_profile = self.PARTNER
        del user_profile["company_name"]

        self._complete_form(user_profile=user_profile, with_submit=True)

        # should not submit form (company_name field is required)
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('account_signup')}")

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
        self.assertEqual(self.driver.current_url, f"{self.live_server_url}{reverse('account_signup')}")

    @patch("lemarche.utils.apis.api_brevo.BrevoContactsApiClient")
    def test_user_submits_signup_form_with_next_param_success_and_redirect(self, mock_brevo_contacts_client):
        mock_client_instance = mock_brevo_contacts_client.return_value
        next_url = f"{reverse('siae:search_results')}?kind=ESAT"
        self._complete_form(
            user_profile=self.SIAE,
            signup_url=f"{reverse('account_signup')}?next={next_url}",
            with_submit=False,
        )
        submit_element = self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']")
        scroll_to_and_click_element(self.driver, submit_element)

        messages = self._assert_signup_success(redirect_url=next_url, user_kind=User.KIND_SIAE)
        self.assertIn("Connexion avec siae@example.com réussie.", messages)
        # assert Brevo contact creation
        mock_client_instance.create_contact.assert_called_once()

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()


class SignupFormTestcase(TestCase):
    """Without integration testing"""

    def setUp(self):
        EXAMPLE_PASSWORD = "c*[gkp`0="
        self.form_data = {
            "accept_rgpd": True,
            "first_name": "Prenom",
            "last_name": "Nom",
            "phone": "0123456789",
            "company_name": "Ma boite",
            "position": "Role important",
            "password1": EXAMPLE_PASSWORD,
            "password2": EXAMPLE_PASSWORD,
        }

    def test_personal_email_buyer(self):
        self.form_data["kind"] = User.KIND_BUYER
        self.form_data["email"] = "buyer@gmail.com"

        form = CustomSignupForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_personnal_email_individual(self):
        """For individuals, or other kind except BUYER, address should not be necessary professional"""
        self.form_data["kind"] = User.KIND_INDIVIDUAL
        self.form_data["email"] = "buyer@gmail.com"

        form = CustomSignupForm(data=self.form_data)
        self.assertTrue(form.is_valid())

    def test_professional_email_buyer(self):
        """This email is a professional one, it should pass"""
        self.form_data["kind"] = User.KIND_INDIVIDUAL
        self.form_data["email"] = "buyer@veryprofessional.com"

        form = CustomSignupForm(data=self.form_data)
        self.assertTrue(form.is_valid())


class SignupEnumerationTest(TestCase):
    """The signup response must not reveal whether an address already has an account (V16)"""

    def setUp(self):
        brevo_patcher = patch("lemarche.utils.apis.api_brevo.BrevoContactsApiClient")
        brevo_patcher.start()
        self.addCleanup(brevo_patcher.stop)
        password = "c*[gkp`0="
        self.form_data = {
            "kind": User.KIND_INDIVIDUAL,
            "accept_rgpd": True,
            "first_name": "Prenom",
            "last_name": "Nom",
            "password1": password,
            "password2": password,
        }

    def signup(self, email):
        return self.client.post(reverse("account_signup"), data=self.form_data | {"email": email})

    @staticmethod
    def emails_to(address):
        """Emails sent to the address (the team is also notified of new accounts)"""
        return [email for email in mail.outbox if address in email.to]

    def test_same_response_for_new_and_existing_address(self):
        UserFactory(email="existing@example.com")

        response_new = self.signup("new@example.com")
        self.client.logout()
        response_existing = self.signup("existing@example.com")

        self.assertEqual(response_new.status_code, 302)
        self.assertEqual(response_existing.status_code, 302)
        self.assertEqual(response_new.url, reverse("account_email_verification_sent"))
        self.assertEqual(response_existing.url, response_new.url)

    def test_new_address_creates_an_unverified_account_without_logging_in(self):
        self.signup("new@example.com")

        user = User.objects.get(email="new@example.com")
        self.assertFalse(EmailAddress.objects.filter(user=user, verified=True).exists())
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(self.emails_to("new@example.com")), 1)

    def test_existing_address_sends_an_email_without_creating_an_account(self):
        existing_user = UserFactory(email="existing@example.com")

        self.signup("existing@example.com")

        self.assertEqual(list(User.objects.all()), [existing_user])
        self.assertNotIn("_auth_user_id", self.client.session)
        emails = self.emails_to("existing@example.com")
        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0].subject, "Votre compte sur le Marché de l'inclusion")
        self.assertIn(reverse("auth:password_reset"), emails[0].body)

    def test_existing_address_is_case_insensitive(self):
        existing_user = UserFactory(email="existing@example.com")

        response = self.signup("Existing@Example.com")

        self.assertEqual(response.url, reverse("account_email_verification_sent"))
        self.assertEqual(list(User.objects.all()), [existing_user])

    def test_unverified_user_must_confirm_the_address_to_log_in(self):
        user = UserFactory(email="unverified@example.com")

        response = self.client.post(reverse("account_login"), data={"login": user.email, "password": DEFAULT_PASSWORD})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("account_email_verification_sent"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(self.emails_to(user.email)), 1)


class LoginViewEnumerationTest(TestCase):
    def test_failed_login_response_does_not_depend_on_account_state(self):
        """
        A failed login should display the same generic error, whether the account exists
        (with or without a password) or not: no user enumeration.
        """
        user_with_password = UserFactory(email="user-with-password@example.com")
        user_without_password = UserFactory(email="user-without-password@example.com")
        # only way to have an empty password field
        User.objects.filter(id=user_without_password.id).update(password="")

        for email in [user_with_password.email, user_without_password.email, "unknown-user@example.com"]:
            with self.subTest(email=email):
                response = self.client.post(reverse("account_login"), {"login": email, "password": "wrong-password"})
                self.assertEqual(response.status_code, 200)
                self.assertNotIn("new_user_without_password", response.context)
                self.assertContains(response, "L’adresse e-mail ou le mot de passe sont incorrects.")
                self.assertNotContains(response, "pas encore défini de mot de passe")


class ConfirmEmailViewTest(TestCase):
    def test_get_confirmation_link_of_another_account_does_not_logout_user(self):
        user = UserFactory()
        other_user = UserFactory()
        email_address = EmailAddress.objects.create(user=other_user, email=other_user.email, primary=True)
        key = EmailConfirmationHMAC(email_address).key
        self.client.force_login(user)

        response = self.client.get(reverse("account_confirm_email", args=[key]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)
        email_address.refresh_from_db()
        self.assertFalse(email_address.verified)

    def confirm(self, user):
        email_address = EmailAddress.objects.create(user=user, email=user.email, primary=True)
        key = EmailConfirmationHMAC(email_address).key
        response = self.client.post(reverse("account_confirm_email", args=[key]))
        email_address.refresh_from_db()
        self.assertTrue(email_address.verified)
        return [str(message) for message in get_messages(response.wsgi_request)]

    def test_siae_user_without_structure_is_invited_to_add_one_once_confirmed(self):
        messages = self.confirm(UserFactory(kind=User.KIND_SIAE))

        self.assertIn(
            "Vous pouvez maintenant ajouter votre structure en cliquant sur "
            f'<a href="{reverse("dashboard_siaes:siae_search_by_siret")}">Ajouter une structure</a>.',
            messages,
        )

    def test_no_invitation_to_add_a_structure_for_other_users(self):
        siae_user_with_structure = UserFactory(kind=User.KIND_SIAE)
        SiaeFactory(users=[siae_user_with_structure])
        for user in [siae_user_with_structure, UserFactory(kind=User.KIND_BUYER)]:
            with self.subTest(kind=user.kind):
                messages = self.confirm(user)
                self.assertFalse([message for message in messages if "Ajouter une structure" in message])


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
        user_siae = create_user_with_verified_email(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('account_login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_login").send_keys(user_siae.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should redirect SIAE to dashboard
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('dashboard:home')}")

    def test_non_siae_user_can_sign_in_and_is_redirected_to_home(self):
        user_buyer = create_user_with_verified_email(email="buyer5@example.com", kind=User.KIND_BUYER)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('account_login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_login").send_keys(user_buyer.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should redirect BUYER to search
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('siae:search_results')}")

    def test_user_can_sign_in_with_email_containing_capital_letters(self):
        create_user_with_verified_email(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('account_login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_login").send_keys("SIAE5@example.com")
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys(DEFAULT_PASSWORD)

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

    def test_user_wrong_credentials_should_see_error_message(self):
        user_siae = create_user_with_verified_email(email="siae5@example.com", kind=User.KIND_SIAE)
        driver = self.driver
        driver.get(f"{self.live_server_url}{reverse('account_login')}")

        driver.find_element(By.CSS_SELECTOR, "input#id_login").send_keys(user_siae.email)
        driver.find_element(By.CSS_SELECTOR, "input#id_password").send_keys("password")

        driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

        # should not submit form
        self.assertEqual(driver.current_url, f"{self.live_server_url}{reverse('account_login')}")
        # error message should be displayed
        messages = driver.find_element(By.CSS_SELECTOR, "section.fr-input-group--error")
        self.assertTrue("L’adresse e-mail ou le mot de passe sont incorrects." in messages.text)

    @classmethod
    def tearDownClass(cls):
        cls.driver.close()
        super().tearDownClass()
