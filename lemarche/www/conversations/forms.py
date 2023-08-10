from django import forms

from lemarche.utils.mtcaptcha import check_captcha_token


class ContactForm(forms.Form):
    first_name = forms.CharField(
        label="Votre prénom", widget=forms.TextInput(attrs={"autofocus": "autofocus"}), required=True
    )
    last_name = forms.CharField(label="Votre nom", required=True)
    email = forms.EmailField(label="Votre email")
    subject = forms.CharField(max_length=200, label="Sujet de la demande")
    body_message = forms.CharField(label="Votre message", widget=forms.Textarea)

    def __init__(self, user=None, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields["first_name"].widget = forms.HiddenInput()
            self.fields["last_name"].widget = forms.HiddenInput()
            self.fields["email"].widget = forms.HiddenInput()

    def clean(self):
        super().clean()
        if not check_captcha_token(self.data):
            raise forms.ValidationError("Le code de protection est incorrect. Veuillez réessayer.")
