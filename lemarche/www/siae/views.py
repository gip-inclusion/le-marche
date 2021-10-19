import csv
import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from lemarche.siaes.models import Siae
from lemarche.www.siae.forms import SiaeSearchForm


CURRENT_SEARCH_QUERY_COOKIE_NAME = "current_search"


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
        results_ordered = filter_form.order_queryset(results)
        return results_ordered

    def get_context_data(self, **kwargs):
        """
        - initialize the form with the query parameters (only if they are present)
        - store the current search query in the session
        - set the paginator range
        """
        context = super().get_context_data(**kwargs)
        if len(self.request.GET.keys()):
            context["form"] = SiaeSearchForm(data=self.request.GET)
        # store the current search query in the session
        current_search_query = self.request.GET.urlencode()
        self.request.session[CURRENT_SEARCH_QUERY_COOKIE_NAME] = current_search_query
        context["current_search_query"] = self.request.session.get(CURRENT_SEARCH_QUERY_COOKIE_NAME, "")
        # display p numbers only from p-4 to p+4 but don"t go <1 or >pages_count
        context["paginator_range"] = range(
            max(context["page_obj"].number - 4, 1), min(context["page_obj"].number + 4, context["paginator"].num_pages)
        )
        # pass the results in json for javascript (leaflet map)
        context["siaes_json"] = serialize(
            "geojson", context["siaes"], geometry_field="coords", fields=("id", "name", "brand", "slug")
        )
        return context


class SiaeSearchResultsDownloadView(LoginRequiredMixin, View):
    http_method_names = ["get"]

    def get_queryset(self):
        """Filter results."""
        filter_form = SiaeSearchForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get(self, request, *args, **kwargs):
        siae_list = self.get_queryset()

        filename = f"liste_structures_{datetime.date.today()}.csv"
        response = HttpResponse(content_type="text/csv", charset="utf-8")
        response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)

        SIAE_FIELDS_TO_EXPORT = [
            "name",
            "brand",
            "siret",  # siret_pretty ?
            "nature",
            "kind",
            "contact_email",
            "contact_phone",
            "contact_website",
            "city",
            "department",
            "region",
            "post_code",
            "is_qpv",
            "sectors",
        ]

        writer = csv.writer(response)
        # header
        writer.writerow([Siae._meta.get_field(field_name).verbose_name for field_name in SIAE_FIELDS_TO_EXPORT])
        # values
        for siae in siae_list:
            siae_row = []
            for field_name in SIAE_FIELDS_TO_EXPORT:
                # Improve display of some fields: ChoiceFields, BooleanFields, ManyToManyFields
                if field_name == "nature":
                    siae_row.append(getattr(siae, f"get_{field_name}_display")())
                elif field_name in ["is_qpv"]:
                    siae_row.append("Oui" if getattr(siae, field_name, None) else "Non")
                elif field_name == "sectors":
                    siae_row.append(siae.sectors_list_to_string())
                else:
                    siae_row.append(getattr(siae, field_name, ""))
            writer.writerow(siae_row)

        return response


class SiaeDetailView(DetailView):
    template_name = "siae/detail.html"
    context_object_name = "siae"
    queryset = Siae.objects.prefetch_related("sectors")

    def get(self, request, *args, **kwargs):
        """
        Overriden to check if maybe the pk was passed instead of the slug
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # TODO post-migration: remove the whole get() override at some point in the future (2022 ?)
            try:
                siae = get_object_or_404(Siae, pk=int(self.kwargs.get("slug")))
                return redirect(reverse_lazy("siae:detail", args=[siae.slug]))
            except:  # noqa
                raise Http404

    def get_context_data(self, **kwargs):
        """
        - add the current search query (e.g. for the breadcrumbs)
        """
        context = super().get_context_data(**kwargs)
        context["current_search_query"] = self.request.session.get(CURRENT_SEARCH_QUERY_COOKIE_NAME, "")
        return context
