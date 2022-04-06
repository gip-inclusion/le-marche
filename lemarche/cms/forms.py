from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from wagtail.admin.forms import WagtailAdminPageForm


class ArticlePageForm(WagtailAdminPageForm):
    def clean(self):
        cleaned_data = super().clean()
        is_body_page = cleaned_data.get("body")
        is_static_page = cleaned_data.get("is_static_page") and cleaned_data.get("template_name")

        if not (is_body_page or is_static_page):
            self.add_error(
                self.error_class(error_class="nonfield"),
                """Vous devez définir un contenu pour l'article ou si c'est une page statique,
                appuyer sur la case à cocher et renseigner un nom de template valide""",
            )

        if is_static_page:
            template_name = cleaned_data.get("template_name")
            try:
                get_template(f"cms/static/{template_name}")
            except TemplateDoesNotExist:
                self.add_error(
                    "template_name",
                    """Vous devez entrer un nom de template qui existe.
                    En cas de soucis n'hésitez pas à contacter un développeur""",
                )
        return cleaned_data
