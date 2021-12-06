import csv
import datetime
from urllib.parse import quote

import xlwt
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.favorites.models import FavoriteList
from lemarche.siaes.models import Siae
from lemarche.utils.export import SIAE_HEADER, generate_siae_row
from lemarche.utils.tracker import extract_meta_from_request, track
from lemarche.www.siaes.forms import SiaeFavoriteForm, SiaeSearchForm


CURRENT_SEARCH_QUERY_COOKIE_NAME = "current_search"


class SiaeSearchResultsView(FormMixin, ListView):
    template_name = "siaes/search_results.html"
    form_class = SiaeSearchForm
    # queryset = Siae.objects.all()
    context_object_name = "siaes"
    paginate_by = 10
    paginator_class = Paginator

    def get_queryset(self):
        """
        Filter results.
        - filter and order using the SiaeSearchForm
        - if the user is authenticated, annotate with favorite info
        """
        filter_form = SiaeSearchForm(data=self.request.GET)
        perimeter = filter_form.get_perimeter()
        results = filter_form.filter_queryset(perimeter)
        results_ordered = filter_form.order_queryset(results, perimeter)
        if self.request.user.is_authenticated:
            results_ordered = results_ordered.annotate_with_user_favorite_lists_count(self.request.user)
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
        perimeter = filter_form.get_perimeter()
        results = filter_form.filter_queryset(perimeter)
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
    queryset = Siae.objects.prefetch_many_to_many().prefetch_many_to_one().prefetch_related("sectors__group")

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

    def get_queryset(self):
        """
        If the user is authenticated, annotate with favorite info
        """
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.annotate_with_user_favorite_lists_count(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        """
        - add the current search query (e.g. for the breadcrumbs)
        """
        context = super().get_context_data(**kwargs)
        context["current_search_query"] = self.request.session.get(CURRENT_SEARCH_QUERY_COOKIE_NAME, "")
        return context


class SiaeFavoriteView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    http_method_names = ["post"]
    template_name = "siaes/_favorite_modal.html"
    form_class = SiaeFavoriteForm
    context_object_name = "siae"
    queryset = Siae.objects.prefetch_related("favorite_lists").all()
    success_message = "La structure a été ajouté à votre liste d'achat."
    success_url = reverse_lazy("siae:search_results")

    def form_valid(self, form):
        """
        We need to:
        - add the Siae to the corresponding FavoriteLists
        - remove the Siae of some FavoriteLists if needed
        - keep track of addition & removal for the success_message
        """
        siae = form.save(commit=False)
        siae_favorite_lists_form = list()

        if self.request.POST.getlist("favorite_lists"):
            for list_id_str in self.request.POST.getlist("favorite_lists"):
                siae_favorite_lists_form.append(int(list_id_str))

        # new favorite_list? create it
        if self.request.POST.get("new_favorite_list"):
            new_favorite_list = FavoriteList.objects.create(
                name=self.request.POST.get("new_favorite_list"),
                user=self.request.user,
            )
            siae_favorite_lists_form.append(new_favorite_list.id)

        # we want to get the list of favorite_lists that were added & removed from the siae
        siae_favorite_lists_before = list(siae.favorite_lists.values_list("id", flat=True))
        siae_favorite_lists_added = list(set(siae_favorite_lists_form).difference(siae_favorite_lists_before))
        user_favorite_lists = list(self.request.user.favorite_lists.values_list("id", flat=True))
        siae_favorite_lists_absent = list(set(user_favorite_lists).difference(siae_favorite_lists_form))
        siae_favorite_lists_removed = list(set(siae_favorite_lists_absent).intersection(siae_favorite_lists_before))

        # update siae.favorite_lists if added & removed
        for list_id in siae_favorite_lists_added:
            siae.favorite_lists.add(list_id)
        for list_id in siae_favorite_lists_removed:
            siae.favorite_lists.remove(list_id)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data, siae, siae_favorite_lists_added, siae_favorite_lists_removed),
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        return super().get_success_url()

    def get_success_message(self, cleaned_data, siae, siae_favorite_lists_added, siae_favorite_lists_removed):
        """Dynamic success message depending if siae was added or removed from favorite lists."""
        success_message = ""
        if len(siae_favorite_lists_added) or len(siae_favorite_lists_removed):
            success_message = f"La structure <strong>{siae.name_display}</strong> a été"
            if len(siae_favorite_lists_added):
                success_message += f" ajoutée à {len(siae_favorite_lists_added)} de vos listes d'achats."
            else:
                success_message += f" supprimée de {len(siae_favorite_lists_removed)} de vos listes d'achats."
        return success_message
