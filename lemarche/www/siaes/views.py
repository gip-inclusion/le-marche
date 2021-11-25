import csv
import datetime
from urllib.parse import quote

import xlwt
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
from lemarche.utils.export import SIAE_HEADER, generate_siae_row
from lemarche.utils.tracker import extract_meta_from_request, track
from lemarche.www.siaes.forms import SiaeSearchForm


CURRENT_SEARCH_QUERY_COOKIE_NAME = "current_search"


class SiaeSearchResultsView(FormMixin, ListView):
    template_name = "siaes/search_results.html"
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
        context["current_search_query_escaped"] = quote(context["current_search_query"])
        # display p numbers only from p-4 to p+4 but don"t go <1 or >pages_count
        context["paginator_range"] = range(
            max(context["page_obj"].number - 4, 1), min(context["page_obj"].number + 4, context["paginator"].num_pages)
        )
        # pass the results in json for javascript (leaflet map)
        context["siaes_json"] = serialize(
            "geojson", context["siaes"], geometry_field="coords", fields=("id", "name", "brand", "slug")
        )
        return context

    def get(self, request, *args, **kwargs):
        # Track search event
        track(
            "backend",
            "directory_search",
            meta=extract_meta_from_request(self.request),
            session_id=request.COOKIES.get("sessionid", None),
        )
        return super().get(request, *args, **kwargs)


class SiaeSearchResultsDownloadView(LoginRequiredMixin, View):
    http_method_names = ["get"]

    def get_queryset(self):
        """Filter results."""
        filter_form = SiaeSearchForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get(self, request, *args, **kwargs):
        """Build and return a CSV or XLS."""
        siae_list = self.get_queryset()

        format = self.request.GET.get("format", "xls")

        if format == "csv":
            filename = f"liste_structures_{datetime.date.today()}.csv"
            response = HttpResponse(content_type="text/csv", charset="utf-8")
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)

            writer = csv.writer(response)

            # header
            writer.writerow(SIAE_HEADER)

            # rows
            for siae in siae_list:
                siae_row = generate_siae_row(siae)
                writer.writerow(siae_row)

        else:  # "xls"
            filename = f"liste_structures_{datetime.date.today()}.xls"
            response = HttpResponse(content_type="application/ms-excel")
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)

            wb = xlwt.Workbook(encoding="utf-8")
            ws = wb.add_sheet("Structures")

            row_number = 0

            # header
            font_style = xlwt.XFStyle()
            font_style.font.bold = True
            for (index, header_item) in enumerate(SIAE_HEADER):
                ws.write(row_number, index, header_item, font_style)
                # set column width
                # ws.col(col_num).width = HEADER[col_num][1]

            # rows
            font_style = xlwt.XFStyle()
            font_style.alignment.wrap = 1
            for siae in siae_list:
                row_number += 1
                siae_row = generate_siae_row(siae)
                for (index, row_item) in enumerate(siae_row):
                    ws.write(row_number, index, row_item, font_style)

            wb.save(response)

        # Track download event
        track(
            "backend",
            "directory_csv",
            meta=extract_meta_from_request(self.request),
            session_id=request.COOKIES.get("sessionid", None),
        )

        return response


class SiaeDetailView(DetailView):
    template_name = "siaes/detail.html"
    context_object_name = "siae"
    queryset = Siae.objects.prefetch_related("sectors", "sectors__group", "networks")

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
