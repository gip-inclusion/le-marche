from django import forms


class ContactForm(forms.Form):
    first_name = forms.CharField(
        label="Votre prénom", widget=forms.TextInput(attrs={"autofocus": "autofocus"}), required=True
    )
    last_name = forms.CharField(label="Votre nom", required=True)
    email = forms.EmailField(label="Votre email")
    subject = forms.CharField(max_length=200, label="Sujet de la demande")
    body_message = forms.CharField(label="Votre message", widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        is_authenticated = kwargs.pop("is_authenticated", False)
        super(ContactForm, self).__init__(*args, **kwargs)
        if is_authenticated:
            self.fields["first_name"].widget = forms.HiddenInput()
            self.fields["last_name"].widget = forms.HiddenInput()
            self.fields["email"].widget = forms.HiddenInput()
