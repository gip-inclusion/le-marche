from django.forms import Media, widgets
from wagtail.admin.staticfiles import versioned_static


class DsfrIconPickerWidget(widgets.TextInput):
    template_name = "content_manager/widgets/dsfr-icon-picker-widget.html"

    def __init__(self, attrs=None):
        default_attrs = {}
        attrs = attrs or {}
        attrs = {**default_attrs, **attrs}
        super().__init__(attrs=attrs)

    @property
    def media(self):
        return Media(
            js=[
                versioned_static("django-dsfr/icon-picker/assets/js/universal-icon-picker.min.js"),
            ],
            css={
                "all": [
                    versioned_static("django-dsfr/icon-picker/assets/stylesheets/universal-icon-picker.css"),
                    versioned_static("dsfr/dist/utility/utility.min.css"),
                ]
            },
        )
