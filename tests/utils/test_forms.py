from django import forms
from django.test import SimpleTestCase
from dsfr.forms import DsfrBaseForm

from lemarche.utils.forms import BoundField


class ExampleForm(forms.Form):
    name = forms.CharField(label="Nom")
    token = forms.CharField(widget=forms.HiddenInput())


class ExampleDsfrForm(DsfrBaseForm):
    name = forms.CharField(label="Nom")


class FormRendererTest(SimpleTestCase):
    def test_plain_forms_use_the_dsfr_bound_field(self):
        self.assertIsInstance(ExampleForm()["name"], BoundField)

    def test_as_field_group_renders_the_dsfr_field_template(self):
        html = ExampleForm()["name"].as_field_group()

        self.assertIn("fr-input-group", html)
        self.assertIn('class="fr-label"', html)
        self.assertIn("fr-input", html)
        self.assertIn("Nom", html)

    def test_as_field_group_of_a_hidden_field_only_renders_the_input(self):
        html = ExampleForm(initial={"token": "abc"})["token"].as_field_group()

        self.assertHTMLEqual(html, '<input type="hidden" name="token" value="abc" id="id_token">')

    def test_dsfr_base_forms_keep_their_dsfr_rendering(self):
        html = ExampleDsfrForm()["name"].as_field_group()

        self.assertIn("fr-input-group", html)
        self.assertIn("Nom", html)
