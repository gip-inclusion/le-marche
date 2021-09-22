from django.core.paginator import Paginator
from django.views.generic import ListView
from django.views.generic.edit import FormMixin

from lemarche.www.siae.forms import SiaeSearchForm


class SiaeSearchResultsView(FormMixin, ListView):
    template_name = "siae/search_results.html"
    form_class = SiaeSearchForm
    # queryset = Siae.objects.all()
    context_object_name = "siaes"
    paginate_by = 10
    paginator_class = Paginator

    def get_queryset(self):
        """Filter results."""
        filter_form = SiaeSearchForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get_context_data(self, **kwargs):
        """Initialize the form with the query parameters."""
        context = super().get_context_data(**kwargs)
        context["form"] = SiaeSearchForm(data=self.request.GET)
        return context
