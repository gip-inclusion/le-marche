from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import CreateView, FormMixin

from lemarche.cms.models import ArticlePage
from lemarche.cms.snippets import ArticleCategory
from lemarche.favorites.models import FavoriteItem, FavoriteList
from lemarche.networks.models import Network
from lemarche.siaes.models import Siae, SiaeUser, SiaeUserRequest
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.users.models import User
from lemarche.utils.s3 import S3Upload
from lemarche.www.dashboard.forms import (
    ProfileEditForm,
    ProfileFavoriteEditForm,
    SiaeClientReferenceFormSet,
    SiaeEditContactForm,
    SiaeEditInfoForm,
    SiaeEditLinksForm,
    SiaeEditOfferForm,
    SiaeEditSearchForm,
    SiaeImageFormSet,
    SiaeLabelFormSet,
    SiaeOfferFormSet,
    SiaeSearchAdoptConfirmForm,
    SiaeSearchBySiretForm,
    SiaeUserRequestForm,
)
from lemarche.www.dashboard.mixins import (
    FavoriteListOwnerRequiredMixin,
    NetworkMemberRequiredMixin,
    SiaeMemberRequiredMixin,
    SiaeUserAndNotMemberRequiredMixin,
    SiaeUserRequiredMixin,
)
from lemarche.www.dashboard.tasks import (
    send_siae_user_request_email_to_assignee,
    send_siae_user_request_response_email_to_initiator,
)
from lemarche.www.siaes.forms import NetworkSiaeFilterForm


SLUG_RESSOURCES_CAT_SIAES = "solutions"
SLUG_RESSOURCES_CAT_BUYERS = "acheteurs"


class DashboardHomeView(LoginRequiredMixin, DetailView):
    # template_name = "dashboard/home.html"
    context_object_name = "user"

    def get_object(self):
        return self.request.user

    def get_template_names(self):
        if self.request.user.kind == User.KIND_SIAE:
            return ["dashboard/home_siae.html"]
        return ["dashboard/home_buyer.html"]

    def get(self, request, *args, **kwargs):
        """
        Update 'dashboard_last_seen_date'
        """
        user = self.request.user
        if user.is_authenticated:
            User.objects.filter(id=user.id).update(dashboard_last_seen_date=timezone.now())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # filter ressources by user kind
        category_slug = None
        if user.kind == User.KIND_SIAE:
            category_slug = SLUG_RESSOURCES_CAT_SIAES
        elif user.kind == User.KIND_BUYER:
            category_slug = SLUG_RESSOURCES_CAT_BUYERS
        article_list = ArticlePage.objects.live().public().order_by("-last_published_at")

        if category_slug:
            try:
                # Look for the blog category by its slug.
                category = ArticleCategory.objects.get(slug=category_slug)
                article_list = article_list.filter(categories__in=[category])
            except Exception:
                category_slug = None

        # set context ressources
        context["current_slug_cat"] = category_slug
        context["last_3_ressources"] = article_list[:3]

        # for specific users
        if user.kind == User.KIND_SIAE:
            siaes = user.siaes.all()
            if siaes:
                context["last_3_tenders"] = Tender.objects.filter_with_siaes(siaes).order_by_deadline_date()[:3]
        else:
            context["last_3_tenders"] = Tender.objects.filter(author=user).order_by_deadline_date()[:3]
            context["user_buyer_count"] = User.objects.filter(kind=User.KIND_BUYER).count()
            context["siae_count"] = Siae.objects.is_live().count()
            context["tender_count"] = Tender.objects.validated().count() + 30  # historic number (before form)
        return context


class ProfileEditView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileEditForm
    template_name = "dashboard/profile_edit.html"
    success_message = "Votre profil a été mis à jour."
    success_url = reverse_lazy("dashboard:home")

    def get_object(self):
        return self.request.user


class ProfileFavoriteListView(LoginRequiredMixin, ListView):
    # form_class = ProfileFavoriteEditForm
    template_name = "dashboard/profile_favorite_list.html"
    queryset = FavoriteList.objects.all()
    context_object_name = "favorite_lists"

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.by_user(user=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProfileFavoriteEditForm()
        return context


class ProfileFavoriteListCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = ProfileFavoriteEditForm
    # success_message = "Votre liste d'achat a été crée avec succès."
    success_url = reverse_lazy("dashboard:profile_favorite_list")

    def form_valid(self, form):
        """Add the User to the FavoriteList."""
        favorite_list = form.save(commit=False)
        favorite_list.user = self.request.user
        favorite_list.save()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data),
        )
        return HttpResponseRedirect(self.success_url)

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre liste d'achat <strong>{cleaned_data['name']}</strong> a été crée avec succès.")


class ProfileFavoriteListDetailView(FavoriteListOwnerRequiredMixin, DetailView):
    template_name = "dashboard/profile_favorite_list_detail.html"
    queryset = FavoriteList.objects.prefetch_related("siaes").all()
    context_object_name = "favorite_list"


class ProfileFavoriteListEditView(FavoriteListOwnerRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = ProfileFavoriteEditForm
    template_name = "siaes/_favorite_list_edit_modal.html"
    success_message = "Votre liste d'achat a été modifiée avec succès."
    # success_url = reverse_lazy("dashboard:profile_favorite_list_detail")

    def get_object(self):
        return get_object_or_404(FavoriteList, slug=self.kwargs.get("slug"))

    def get_success_url(self):
        return reverse_lazy("dashboard:profile_favorite_list_detail", args=[self.kwargs.get("slug")])


class ProfileFavoriteListDeleteView(FavoriteListOwnerRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "siaes/_favorite_list_delete_modal.html"
    model = FavoriteList
    # success_message = "Votre liste d'achat a été supprimée avec succès."
    success_url = reverse_lazy("dashboard:profile_favorite_list")

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre liste d'achat <strong>{self.object.name}</strong> a été supprimée avec succès.")


class ProfileFavoriteItemDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    # FavoriteListOwnerRequiredMixin  # doesn't work because we don't have the FavoriteList slug
    template_name = "siaes/_favorite_item_remove_modal.html"
    model = FavoriteItem
    # success_message = "La structure a été supprimée de votre liste d'achat avec succès."
    success_url = reverse_lazy("dashboard:profile_favorite_list_detail")

    def get_object(self):
        """
        - there should theoretically be only 1 Siae per user's lists (an Siae cannot belong to other list)
        - in the future it could be possible to add an Siae to multiple user lists
        """
        # try:
        #     favorite_list = FavoriteList.objects.get(slug=self.kwargs.get("slug"))
        #     siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        #     return get_object_or_404(FavoriteItem, favorite_list=favorite_list, siae=siae)
        # except:  # noqa
        #     raise Http404
        siae = Siae.objects.get(slug=self.kwargs.get("siae_slug"))
        return get_object_or_404(FavoriteItem, favorite_list__user=self.request.user, siae=siae)

    def get_success_url(self):
        """Redirect to the previous page."""
        request_referer = self.request.META.get("HTTP_REFERER", "")
        if request_referer:
            return request_referer
        return super().get_success_url()

    def get_success_message(self, cleaned_data):
        return mark_safe(
            f"<strong>{self.object.siae.name_display}</strong> a été supprimée de votre liste d'achat avec succès."
        )


class ProfileNetworkDetailView(NetworkMemberRequiredMixin, DetailView):
    template_name = "dashboard/profile_network_detail.html"
    queryset = Network.objects.prefetch_related("siaes").all()
    context_object_name = "network"


class ProfileNetworkSiaeListView(NetworkMemberRequiredMixin, FormMixin, ListView):
    template_name = "dashboard/profile_network_siae_list.html"
    form_class = NetworkSiaeFilterForm
    queryset = Siae.objects.prefetch_related("networks").all()
    context_object_name = "siaes"

    def get_queryset(self):
        qs = super().get_queryset()
        self.network = Network.objects.get(slug=self.kwargs.get("slug"))
        qs = qs.filter(networks__in=[self.network]).with_tender_stats().annotate_with_brand_or_name(with_order_by=True)
        self.filter_form = NetworkSiaeFilterForm(data=self.request.GET)
        qs = self.filter_form.filter_queryset(qs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        siae_search_form = self.filter_form if self.filter_form else NetworkSiaeFilterForm(data=self.request.GET)
        context["form"] = siae_search_form
        return context


class ProfileNetworkSiaeTenderListView(NetworkMemberRequiredMixin, ListView):
    template_name = "dashboard/profile_network_siae_tender_list.html"
    queryset = TenderSiae.objects.select_related("tender", "siae").all()
    context_object_name = "tendersiaes"
    status = None

    def get(self, request, status=None, *args, **kwargs):
        """
        - check that both the Siae & the Network exist
        - check that the Siae belongs to the Network
        """
        self.status = status
        if "slug" in self.kwargs:
            self.network = get_object_or_404(Network, slug=self.kwargs.get("slug"))
            if "siae_slug" in self.kwargs:
                self.siae = get_object_or_404(Siae.objects.with_tender_stats(), slug=self.kwargs.get("siae_slug"))
                if self.siae not in self.network.siaes.all():
                    return redirect("dashboard:profile_network_siae_list", slug=self.network.slug)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(siae=self.siae)
        if self.status:
            if self.status == "DISPLAY":
                qs = qs.filter(detail_display_date__isnull=False)
            elif self.status == "CONTACT-CLICK":
                qs = qs.filter(detail_contact_click_date__isnull=False)
        else:  # default
            qs = qs.filter(email_send_date__isnull=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        context["siae"] = self.siae
        return context


class ProfileNetworkTenderListView(NetworkMemberRequiredMixin, ListView):
    template_name = "dashboard/profile_network_tender_list.html"
    queryset = Tender.objects.all()
    context_object_name = "tenders"
    paginate_by = 10
    paginator_class = Paginator

    def get_queryset(self):
        qs = super().get_queryset()
        self.network = Network.objects.prefetch_related("siaes").get(slug=self.kwargs.get("slug"))
        self.network_siaes = self.network.siaes.all()
        qs = qs.prefetch_many_to_many().select_foreign_keys()
        qs = qs.filter_with_siaes(self.network_siaes)
        qs = qs.with_network_siae_stats(self.network_siaes)
        qs = qs.order_by_deadline_date()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        return context


class ProfileNetworkTenderSiaeListView(NetworkMemberRequiredMixin, ListView):
    template_name = "dashboard/profile_network_tender_siae_list.html"
    queryset = TenderSiae.objects.select_related("tender", "siae").all()
    context_object_name = "tendersiaes"
    status = None

    def get(self, request, status=None, *args, **kwargs):
        """
        - fetch the Network & the Tender
        """
        self.status = status
        if "slug" in self.kwargs:
            self.network = get_object_or_404(Network, slug=self.kwargs.get("slug"))
            if "tender_slug" in self.kwargs:
                self.network_siaes = self.network.siaes.all()
                self.tender = get_object_or_404(
                    Tender.objects.validated().with_network_siae_stats(self.network_siaes),
                    slug=self.kwargs.get("tender_slug"),
                )
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(tender=self.tender).filter(email_send_date__isnull=False)
        qs = qs.filter(siae__in=self.network.siaes.all())
        if self.status:
            if self.status == "CONTACT-CLICK":
                qs = qs.filter(detail_contact_click_date__isnull=False)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        context["tender"] = self.tender
        return context


class SiaeSearchBySiretView(SiaeUserRequiredMixin, FormMixin, ListView):
    form_class = SiaeSearchBySiretForm
    template_name = "dashboard/siae_search_by_siret.html"
    context_object_name = "siaes"
    # queryset =

    def get_queryset(self):
        """Filter results."""
        filter_form = SiaeSearchBySiretForm(data=self.request.GET)
        results = filter_form.filter_queryset()
        return results

    def get_context_data(self, **kwargs):
        """
        - initialize the form with the query parameters (only if they are present)
        """
        context = super().get_context_data(**kwargs)
        if len(self.request.GET.keys()):
            context["form"] = SiaeSearchBySiretForm(data=self.request.GET)
        return context


class SiaeSearchAdoptConfirmView(SiaeUserAndNotMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeSearchAdoptConfirmForm
    template_name = "dashboard/siae_search_adopt_confirm.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Rattachement confirmé ! Vous pouvez dès à présent mettre à jour sa fiche."

    def get_context_data(self, **kwargs):
        """
        - check if there isn't any pending SiaeUserRequest
        """
        context = super().get_context_data(**kwargs)
        siae_user_pending_request = self.object.siaeuserrequest_set.initiator(self.request.user).pending()
        context["siae_user_pending_request"] = siae_user_pending_request
        return context

    def form_valid(self, form):
        """
        - Siae with user? add the User to the Siae
        - Siae with existing user(s)? go through the invitation workflow
        """
        if not self.object.users.count():
            self.object.users.add(self.request.user)
            return super().form_valid(form)
        else:
            # create SiaeUserRequest + send request email to assignee
            siae_user_request = SiaeUserRequest.objects.create(
                siae=self.object,
                initiator=self.request.user,
                assignee=self.object.users.first(),
                logs=[{"action": "create", "timestamp": timezone.now().isoformat()}],
            )
            send_siae_user_request_email_to_assignee(siae_user_request)
            success_message = (
                f"La demande a été envoyée à {self.object.users.first().full_name}.<br />"
                f"<i>Cet utilisateur ne fait plus partie de la structure ? <a href=\"{reverse_lazy('dashboard:siae_search_by_siret')}?siret={self.object.siret}\">Contactez le support</a></i>"  # noqa
            )
            messages.add_message(self.request, messages.SUCCESS, success_message)
            return HttpResponseRedirect(reverse_lazy("dashboard:home"))

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit", args=[self.kwargs.get("slug")])


class SiaeUsersView(SiaeMemberRequiredMixin, DetailView):
    template_name = "dashboard/siae_users.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()

    def get_context_data(self, **kwargs):
        """
        - check if there isn't any pending SiaeUserRequest
        """
        context = super().get_context_data(**kwargs)
        siae_user_pending_request = self.object.siaeuserrequest_set.assignee(self.request.user).pending()
        context["siae_user_pending_request"] = siae_user_pending_request
        return context


class SiaeEditSearchView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditSearchForm
    template_name = "dashboard/siae_edit_search.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_search", args=[self.kwargs.get("slug")])


class SiaeEditInfoView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditInfoForm
    template_name = "dashboard/siae_edit_info.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_context_data(self, **kwargs):
        """
        - pass s3 image upload config
        - init label form
        """
        context = super().get_context_data(**kwargs)
        s3_upload = S3Upload(kind="siae_logo")
        context["s3_form_values_siae_logo"] = s3_upload.form_values
        context["s3_upload_config_siae_logo"] = s3_upload.config
        if self.request.POST:
            context["label_formset"] = SiaeLabelFormSet(self.request.POST, instance=self.object)
        else:
            context["label_formset"] = SiaeLabelFormSet(instance=self.object)
        context["last_3_siae_content_filled_full"] = (
            Siae.objects.with_content_filled_stats()
            .filter(content_filled_full=True)
            .exclude(id=self.object.id)
            .order_by("-updated_at")[:3]
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        label_formset = SiaeLabelFormSet(self.request.POST, instance=self.object)
        if form.is_valid() and label_formset.is_valid():
            return self.form_valid(form, label_formset)
        else:
            return self.form_invalid(form, label_formset)

    def form_valid(self, form, label_formset):
        self.object = form.save()
        label_formset.instance = self.object
        label_formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, label_formset):
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_info", args=[self.kwargs.get("slug")])


class SiaeEditOfferView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditOfferForm
    template_name = "dashboard/siae_edit_offer.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_context_data(self, **kwargs):
        """
        - init forms
        - pass s3 image upload config
        """
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["offer_formset"] = SiaeOfferFormSet(self.request.POST, instance=self.object)
            context["client_reference_formset"] = SiaeClientReferenceFormSet(self.request.POST, instance=self.object)
            context["image_formset"] = SiaeImageFormSet(self.request.POST, instance=self.object)
        else:
            context["offer_formset"] = SiaeOfferFormSet(instance=self.object)
            context["client_reference_formset"] = SiaeClientReferenceFormSet(instance=self.object)
            context["image_formset"] = SiaeImageFormSet(instance=self.object)
        s3_upload_client_reference_logo = S3Upload(kind="client_reference_logo")
        context["s3_form_values_client_reference_logo"] = s3_upload_client_reference_logo.form_values
        context["s3_upload_config_client_reference_logo"] = s3_upload_client_reference_logo.config
        s3_upload_siae_image = S3Upload(kind="siae_image")
        context["s3_form_values_siae_image"] = s3_upload_siae_image.form_values
        context["s3_upload_config_siae_image"] = s3_upload_siae_image.config
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        offer_formset = SiaeOfferFormSet(self.request.POST, instance=self.object)
        client_reference_formset = SiaeClientReferenceFormSet(self.request.POST, instance=self.object)
        image_formset = SiaeImageFormSet(self.request.POST, instance=self.object)
        if (
            form.is_valid()
            and offer_formset.is_valid()
            and client_reference_formset.is_valid()
            and image_formset.is_valid()
        ):
            return self.form_valid(form, offer_formset, client_reference_formset, image_formset)
        else:
            return self.form_invalid(form, offer_formset, client_reference_formset, image_formset)

    def form_valid(self, form, offer_formset, client_reference_formset, image_formset):
        self.object = form.save()
        offer_formset.instance = self.object
        offer_formset.save()
        client_reference_formset.instance = self.object
        client_reference_formset.save()
        image_formset.instance = self.object
        image_formset.save()
        return super().form_valid(form)

    def form_invalid(self, form, offer_formset, client_reference_formset, image_formset):
        return self.render_to_response(self.get_context_data())

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_offer", args=[self.kwargs.get("slug")])


class SiaeEditLinksView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditLinksForm
    template_name = "dashboard/siae_edit_links.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_links", args=[self.kwargs.get("slug")])


class SiaeEditContactView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditContactForm
    template_name = "dashboard/siae_edit_contact.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_edit_contact", args=[self.kwargs.get("slug")])


class SiaeUserRequestConfirm(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeUserRequestForm
    template_name = "siaes/_siae_user_request_confirm_modal.html"
    context_object_name = "siaeuserrequest"
    queryset = SiaeUserRequest.objects.all()
    success_message = "L'utilisateur a été rattaché à votre structure."
    # success_url = reverse_lazy("dashboard:siae_users")

    def get_object(self):
        return get_object_or_404(SiaeUserRequest, id=self.kwargs.get("siaeuserrequest_id"))

    def form_valid(self, form):
        """
        - add user to Siae
        - update SiaeUserRequest
        - notify user
        """
        self.object.siae.users.add(self.object.initiator)
        self.object.response = True
        self.object.response_date = timezone.now()
        self.object.logs.append({"action": "response_true", "timestamp": self.object.response_date.isoformat()})
        self.object.save()
        send_siae_user_request_response_email_to_initiator(self.object, response=True)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_users", args=[self.kwargs.get("slug")])


class SiaeUserRequestCancel(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeUserRequestForm
    template_name = "siaes/_siae_user_request_cancel_modal.html"
    context_object_name = "siaeuserrequest"
    queryset = SiaeUserRequest.objects.all()
    success_message = "L'utilisateur sera informé de votre refus."
    # success_url = reverse_lazy("dashboard:siae_users")

    def get_object(self):
        return get_object_or_404(SiaeUserRequest, id=self.kwargs.get("siaeuserrequest_id"))

    def form_valid(self, form):
        """
        - update SiaeUserRequest
        - notify user
        """
        self.object.response = False
        self.object.response_date = timezone.now()
        self.object.logs.append({"action": "response_false", "timestamp": self.object.response_date.isoformat()})
        self.object.save()
        send_siae_user_request_response_email_to_initiator(self.object, response=False)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_users", args=[self.kwargs.get("slug")])


class SiaeUserDelete(SiaeMemberRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "siaes/_siae_user_delete_modal.html"
    model = SiaeUser
    # success_message = "L'utilisateur a été supprimé de votre structure."
    # success_url = reverse_lazy("dashboard:siae_users")

    def get_object(self):
        siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return get_object_or_404(SiaeUser, siae=siae, id=self.kwargs.get("siaeuser_id"))

    def get_success_url(self):
        return reverse_lazy("dashboard:siae_users", args=[self.kwargs.get("slug")])

    def get_success_message(self, cleaned_data):
        return mark_safe(
            f"L'utilisateur <strong>{self.object.user.full_name}</strong> a été supprimé de votre structure avec succès."  # noqa
        )
