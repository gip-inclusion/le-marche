from django import forms


class CustomSelectMultiple(forms.CheckboxSelectMultiple):
    template_name = "includes/_widget_custom_multiselect.html"

    def get_context(self, name, value, attrs):
        if attrs is None:
            attrs = {}
        if "id" not in attrs:
            attrs["id"] = f"id_{name}"
        context = super().get_context(name, value, attrs)
        context["widget"]["options"] = self.choices
        context["widget"]["value"] = value
        return context
