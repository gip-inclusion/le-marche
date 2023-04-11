from django import forms

from lemarche.favorites.models import FavoriteList


class FavoriteListEditForm(forms.ModelForm):
    class Meta:
        model = FavoriteList
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update({"placeholder": "Entretien des locaux, achat de masque…"})
