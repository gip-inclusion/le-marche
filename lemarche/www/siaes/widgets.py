from django.forms import widgets


class CustomLocationWidget(widgets.SelectMultiple):
    template_name = "siaes/widgets/location_widget.html"

    def get_context(self, name, value, attrs):
        _context = super().get_context(name, value, attrs)
        _context["is_disabled"] = self.is_disabled()
        return _context

    def is_disabled(self):
        return self.attrs.get("disabled", False)
