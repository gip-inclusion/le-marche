from django import forms


class ContactForm(forms.Form):
    email = forms.EmailField(label="Votre email")
    subject = forms.CharField(max_length=200, label="Sujet de la demande")
    body_message = forms.CharField(label="Votre message", widget=forms.Textarea)
