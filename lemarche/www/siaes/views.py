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
from django.views.generic import DetailView, ListView, TemplateView, UpdateView
from django.views.generic.base import View
from django.views.generic.edit import FormMixin

from lemarche.conversations.models import Conversation
from lemarche.favorites.models import FavoriteList
from lemarche.siaes import constants as siae_constants
from lemarche.siaes.models import Siae
from lemarche.utils import settings_context_processors
from lemarche.utils.export import export_siae_to_csv, export_siae_to_excel
from lemarche.utils.s3 import API_CONNECTION_DICT
from lemarche.utils.urls import get_domain_url, get_encoded_url_from_params
from lemarche.www.conversations.forms import ContactForm
from lemarche.www.siaes.forms import SiaeFavoriteForm, SiaeFilterForm, SiaeSiretFilterForm


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
    form_class = SiaeFilterForm
    filter_form = None
    context_object_name = "siaes"
    paginate_by = 20
    paginator_class = Paginator

    def get_filter_form(self):
        if not self.filter_form:
            user = self.request.user
            self.filter_form = SiaeFilterForm(data=self.request.GET, advanced_search=user.is_authenticated)
        return self.filter_form

    def get_queryset(self):
        """
        Filter results.
        - filter and order using the SiaeFilterForm
        - if the user is authenticated, annotate with favorite info
        """
        user = self.request.user
        filter_form = self.get_filter_form()
        results = filter_form.filter_queryset()
        results_ordered = filter_form.order_queryset(results)
        if user.is_authenticated:
            results_ordered = results_ordered.with_in_user_favorite_list_stats(user)
        return results_ordered

    def get_mailto_share_url(self):
        """
        Function to generate url for share search with url
        """
        user = self.request.user
        user_full_name = "" if not user.is_authenticated else user.full_name
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
        siae_search_form = self.get_filter_form()
        context["form"] = siae_search_form
        context["url_share_list"] = self.get_mailto_share_url()
        if len(self.request.GET.keys()):
            context["is_advanced_search"] = siae_search_form.is_advanced_search()
            if siae_search_form.is_valid():
                current_perimeters = siae_search_form.cleaned_data.get("perimeters")
                if current_perimeters:
                    context["current_perimeters"] = list(current_perimeters.values("id", "slug", "name"))
                current_locations = siae_search_form.cleaned_data.get("locations")
                if current_locations:
                    context["current_locations"] = list(current_locations.values("id", "slug", "name"))
                current_sectors = siae_search_form.cleaned_data.get("sectors")
                if current_sectors:
                    context["current_sectors"] = list(current_sectors.values("id", "slug", "name"))
                    context["current_sector_groups"] = list(set(sector.group for sector in current_sectors))

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


class SiaeSearchResultsDownloadView(LoginRequiredMixin, View):
    http_method_names = ["get"]

    def get_queryset(self):
        """
        Filter results.
        """
        filter_form = SiaeFilterForm(data=self.request.GET)
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
            value for (key, value) in self.request.GET.items() if ((key not in ["page", "format"]) and value)
        ]

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


class SiaeDetailView(FormMixin, DetailView):
    template_name = "siaes/detail.html"
    context_object_name = "siae"
    form_class = ContactForm
    success_url = reverse_lazy("siae:detail")
    queryset = (
        Siae.objects.prefetch_many_to_many()
        .prefetch_many_to_one()
        .prefetch_related("groups")
        .prefetch_related("activities__sector__group")
        .prefetch_related("activities__locations")
    )

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

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form=form, siae=self.object)
        else:
            return self.form_invalid(form=form, siae=self.object)

    def get_success_url(self) -> str:
        success_url = reverse_lazy("siae:detail", args=[self.get_object().slug])
        return success_url

    def form_valid(self, form: ContactForm, siae: Siae):
        """If the form is valid, redirect to the supplied URL."""
        cleaned_data = form.cleaned_data
        conv = Conversation.objects.create(
            title=cleaned_data.get("subject"),
            sender_user=self.request.user if self.request.user.is_authenticated else None,
            sender_email=cleaned_data.get("email"),
            sender_first_name=cleaned_data.get("first_name"),
            sender_last_name=cleaned_data.get("last_name"),
            siae=siae,
            initial_body_message=cleaned_data.get("body_message"),
        )
        messages.add_message(
            self.request,
            messages.SUCCESS,
            f'Votre demande "{conv.title}" a bien été envoyée, vous recevrez bientôt un retour du prestataire',
        )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form: ContactForm, siae: Siae):
        return self.render_to_response(self.get_context_data())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user

        if user.is_authenticated:
            initial["email"] = user.email
            initial["first_name"] = user.first_name
            initial["last_name"] = user.last_name

        return initial

    def get_queryset(self):
        """
        If the user is authenticated, annotate with favorite info
        """
        qs = super().get_queryset()
        if self.request.user.is_authenticated:
            qs = qs.with_in_user_favorite_list_stats(self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        """
        - add the current search query (e.g. for the breadcrumbs)
        """
        context = super().get_context_data(**kwargs)
        context["current_search_query"] = self.request.session.get(CURRENT_SEARCH_QUERY_COOKIE_NAME, "")
        context["inbound_email_is_activated"] = settings.INBOUND_EMAIL_IS_ACTIVATED
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {
                    "title": "Recherche",
                    "url": f"{reverse_lazy('siae:search_results')}?{context['current_search_query']}",
                },
            ],
            "current": self.get_object().name_display,
        }
        return context


class SiaeFavoriteView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    http_method_names = ["post"]
    template_name = "favorites/_favorite_item_add_modal.html"
    form_class = SiaeFavoriteForm
    context_object_name = "siae"
    queryset = Siae.objects.prefetch_related("favorite_lists").all()
    success_url = reverse_lazy("siae:search_results")

    def get_form_kwargs(self):
        """Pass the current user to the form."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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

    def form_invalid(self, form):
        messages.add_message(
            self.request, messages.ERROR, "Erreur, cette structure est déjà liée à une liste de favoris."
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


class SiaeSiretSearchView(TemplateView):
    template_name = "siaes/siret_search_results.html"
    # Custom from KIND_INSERTION_CHOICES, no SEP
    IAE_LIST = [
        siae_constants.KIND_EI,
        siae_constants.KIND_AI,
        siae_constants.KIND_ACI,
        siae_constants.KIND_ETTI,
        siae_constants.KIND_EITI,
        siae_constants.KIND_GEIQ,
    ]
    HANDICAP_LIST = siae_constants.KIND_HANDICAP_LIST

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.filter_form = SiaeSiretFilterForm(data=request.GET)

    def find_supplier_by_siret(self, siret: str):
        if Siae.objects.filter(siret=siret).exists():
            siae = Siae.objects.get(siret=siret)
            if siae.kind in self.IAE_LIST:
                return (
                    "Votre fournisseur est un fournisseur inclusif relevant de l’Insertion par"
                    " l’Activité Économique (IAE) et appartient de facto à l’Economie Sociale et Solidaire (ESS)."
                )
            if siae.kind in self.HANDICAP_LIST:
                return (
                    "Votre fournisseur est un fournisseur inclusif relevant du secteur du Handicap"
                    " et appartient de facto à l’Economie Sociale et Solidaire (ESS)."
                )

        # ESUS
        elif False:
            return (
                "Votre fournisseur est labellisé ESUS (Entreprise Solidaire d’Utilité Sociale)"
                " et appartient de facto à l’Economie Sociale et Solidaire (ESS)."
            )
        # ESS
        elif False:
            return (
                (
                    " Votre fournisseur relève de l’Économie Sociale et Solidaire (ESS)"
                    " mais n’est pas un fournisseur inclusif."
                ),
            )
        return (
            "Ce fournisseur n’est pas un fournisseur inclusif"
            " et n’appartient pas à l’Économie Sociale et Solidaire (ESS)."
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.filter_form

        if self.filter_form.is_valid():
            message = self.find_supplier_by_siret(self.filter_form.cleaned_data.get("siret"))
        else:
            message = ""

        ctx["status_message"] = message
        return ctx
