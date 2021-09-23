from django.core.paginator import Paginator
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from lemarche.siaes.models import Siae
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
        # display p numbers only from p-4 to p+4 but don't go <1 or >pages_count
        context["paginator_range"] = range(
            max(context["page_obj"].number - 4, 1), min(context["page_obj"].number + 4, context["paginator"].num_pages)
        )
        return context


class SiaeDetailView(DetailView):
    template_name = "siae/detail.html"
    context_object_name = "siae"
    queryset = Siae.objects.prefetch_related("sectors")
