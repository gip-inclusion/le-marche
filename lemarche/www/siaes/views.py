import csv
from datetime import date
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.favorites.models import FavoriteList
from lemarche.siaes.models import Siae
from lemarche.utils.export import export_siae_to_csv, export_siae_to_excel
from lemarche.utils.s3 import API_CONNECTION_DICT
from lemarche.utils.urls import get_domain_url, get_encoded_url_from_params
from lemarche.www.auth.tasks import add_to_contact_list
from lemarche.www.siaes.forms import SiaeDownloadForm, SiaeFavoriteForm, SiaeSearchForm, SiaeShareForm


CURRENT_SEARCH_QUERY_COOKIE_NAME = "current_search"
# TODO: how to avoid hard-coded sector values like these?
SECTOR_TRAITEUR_SLUG = "traiteur"
SECTOR_GROUP_HYGIERE_SLUG_LIST = [
    "nettoyage-specifique-chantiers-parkings-6",
    "nettoyage-de-vehicules-12",
    "nettoyage-de-locaux-16",
    "produits-dentretien-et-desinfectants-29",
    "articles-protection-covid-19",
    "autre-56",
    "nettoyage-urbain",
    "nettoyage-industriel",
]


class SiaeSearchResultsView(FormMixin, ListView):
    template_name = "siaes/search_results.html"
    form_class = SiaeSearchForm
    # queryset = Siae.objects.all()
    context_object_name = "siaes"
    paginate_by = 20
    paginator_class = Paginator

    def get_queryset(self):
        """
        Filter results.
        - filter and order using the SiaeSearchForm
        - if the user is authenticated, annotate with favorite info
        """
        self.filter_form = SiaeSearchForm(data=self.request.GET)
        results = self.filter_form.filter_queryset()
        results_ordered = self.filter_form.order_queryset(results)
        if self.request.user.is_authenticated:
            results_ordered = results_ordered.annotate_with_user_favorite_list_count(self.request.user)
        return results_ordered

    def get_mailto_share_url(self):
        """Function to generate url for share search with url

        Returns:
            _type_: _description_
        """
        user_full_name = "" if not self.request.user.is_authenticated else self.request.user.full_name
        params = {
            "subject": "Voici une liste de prestataires inclusifs",
            "bcc": settings.CONTACT_EMAIL,
            "body": "Bonjour,\n\n"
            + "Vous pouvez consulter cette liste de prestataires inclusifs dans le cadre de votre besoin de sous-traitance "  # noqa
            + f"à l'adresse suivante : https://{get_domain_url()}{self.request.get_full_path()} \n\n"
            + user_full_name,
        }
        return get_encoded_url_from_params(params)  # encode to avoid spam from mailto

    def get_context_data(self, **kwargs):
        """
        - initialize the form with the query parameters (only if they are present)
        - store the current search query in the session
        - set the paginator range
        """
        context = super().get_context_data(**kwargs)
        context["position_promote_tenders"] = [5, 15]
        siae_search_form = self.filter_form if self.filter_form else SiaeSearchForm(data=self.request.GET)
        context["form"] = siae_search_form
        context["form_download"] = SiaeDownloadForm(data=self.request.GET)
        context["form_share"] = SiaeShareForm(data=self.request.GET, user=self.request.user)
        context["url_share_list"] = self.get_mailto_share_url()
        if len(self.request.GET.keys()):
            if siae_search_form.is_valid():
                current_perimeters = siae_search_form.cleaned_data.get("perimeters")
                if current_perimeters:
                    context["current_perimeters"] = list(current_perimeters.values("id", "slug", "name"))

                current_sectors = siae_search_form.cleaned_data.get("sectors")
                if current_sectors:
                    context["current_sectors"] = list(current_sectors.values("id", "slug", "name"))

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
        """
        Additional actions:
        - add buyer to contact list
        - add buyer who searched for sector 'traiteur' to contact list
        - add buyer who searched for sector 'nettoyage' to contact list
        """
        self.object_list = self.get_queryset()
        user = request.user
        context = self.get_context_data()
        if user.is_authenticated:
            if user.kind == user.KIND_BUYER:
                add_to_contact_list(user, "buyer_search")
                if "current_sectors" in context:
                    if next(
                        (sector for sector in context["current_sectors"] if sector["slug"] == SECTOR_TRAITEUR_SLUG),
                        False,
                    ):
                        add_to_contact_list(user, "buyer_search_traiteur")
                    if next(
                        (
                            sector
                            for sector in context["current_sectors"]
                            if sector["slug"] in SECTOR_GROUP_HYGIERE_SLUG_LIST
                        ),
                        False,
                    ):
                        add_to_contact_list(user, "buyer_search_nettoyage")
        return self.render_to_response(context)


class SiaeSearchResultsDownloadView(LoginRequiredMixin, View):
    http_method_names = ["get"]

    def get_queryset(self):
        """
        Filter results.
        """
        filter_form = SiaeDownloadForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get(self, request, *args, **kwargs):
        """
        Build and return a CSV or XLS.
        """
        siae_list = self.get_queryset()
        format = self.request.GET.get("format", "xls")
        with_contact_info = True if self.request.GET.get("tender", None) else False
        filename = f"liste_structures_{date.today()}"
        filename_with_extension = f"{filename}.{format}"

        # we check if there are any search filters
        request_params = [
            value
            for (key, value) in self.request.GET.items()
            if ((key not in ["marche_benefits", "download_source", "page", "format"]) and value)
        ]

        user = self.request.user
        if user.kind == user.KIND_BUYER:
            add_to_contact_list(user, "buyer_download")

        # no search filters -> the user wants to download the whole list -> serve the generated file stored on S3
        if not len(request_params):
            file_path = f"{API_CONNECTION_DICT['endpoint_url']}/{settings.S3_STORAGE_BUCKET_NAME}/{settings.SIAE_EXPORT_FOLDER_NAME}/{filename_with_extension}"  # noqa
            response = HttpResponseRedirect(file_path)

        else:
            if format == "csv":
                response = HttpResponse(content_type="text/csv", charset="utf-8")
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename_with_extension)

                writer = csv.writer(response)
                export_siae_to_csv(writer, siae_list, with_contact_info)

            else:  # "xls"
                response = HttpResponse(content_type="application/ms-excel")
                response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename_with_extension)

                wb = export_siae_to_excel(siae_list, with_contact_info)
                wb.save(response)

        # HttpResponse doesn't have a context. so we pass the data via the response header
        response["Context-Data-Results-Count"] = siae_list.count()
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
        # if self.request.user.is_authenticated:
        #     qs = qs.annotate_with_user_favorite_list_count(self.request.user)
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
    template_name = "favorites/_favorite_item_add_modal.html"
    form_class = SiaeFavoriteForm
    context_object_name = "siae"
    queryset = Siae.objects.prefetch_related("favorite_lists").all()
    # success_message = "La structure a été ajoutée à votre liste d'achat."
    success_url = reverse_lazy("siae:search_results")

    def form_valid(self, form):
        """
        We need to:
        - add the Siae to the corresponding FavoriteLists
        - remove the Siae of some FavoriteLists if needed
        - keep track of addition & removal for the success_message
        """
        siae = form.save(commit=False)
        favorite_list = None

        if self.request.POST.get("action") == "add":
            if self.request.POST.get("favorite_list"):
                favorite_list = FavoriteList.objects.get(id=self.request.POST.get("favorite_list"))

        # new favorite_list? create it
        elif self.request.POST.get("action") == "create":
            if self.request.POST.get("new_favorite_list"):
                favorite_list = FavoriteList.objects.create(
                    name=self.request.POST.get("new_favorite_list"),
                    user=self.request.user,
                )

        siae.favorite_lists.add(favorite_list)

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data, siae, favorite_list),
        )
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        return super().get_success_url()

    def get_success_message(self, cleaned_data, siae, favorite_list):
        return mark_safe(
            f"<strong>{siae.name_display}</strong> a été ajoutée à "
            f"votre liste d'achat <strong>{favorite_list.name}</strong>."
        )
