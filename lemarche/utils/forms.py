from django.forms.renderers import TemplatesSetting
from dsfr.forms import DsfrBoundField


class BoundField(DsfrBoundField):
    """
    Renders {{ field.as_field_group }} with the DSFR field templates in every form, like the former
    {% dsfr_form_field field %} tag (deprecated since django-dsfr 3.5), not only in DsfrBaseForm subclasses.
    """

    def as_field_group(self):
        # Fields whose widget is hidden (sometimes depending on the context) only render their input
        if self.is_hidden:
            return self.as_hidden()
        return super().as_field_group()


class FormRenderer(TemplatesSetting):
    bound_field_class = BoundField
