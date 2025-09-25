from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes.models import Siae, SiaeActivity, SiaeUser, SiaeUserRequest
from lemarche.utils import settings_context_processors
from lemarche.utils.apis import api_brevo
from lemarche.utils.mixins import SiaeMemberRequiredMixin, SiaeUserAndNotMemberRequiredMixin, SiaeUserRequiredMixin
from lemarche.utils.s3 import S3Upload
from lemarche.www.dashboard_siaes.forms import (
    SiaeActivityForm,
    SiaeClientReferenceFormSet,
    SiaeEditContactForm,
    SiaeEditInfoForm,
    SiaeEditOfferForm,
    SiaeImageFormSet,
    SiaeLabelOldFormSet,
    SiaeOfferFormSet,
    SiaeSearchAdoptConfirmForm,
    SiaeSearchBySiretForm,
    SiaeUserRequestForm,
)
from lemarche.www.dashboard_siaes.tasks import (
    send_siae_user_request_email_to_assignee,
    send_siae_user_request_response_email_to_initiator,
)


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
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")},
            ],
            "current": "Rechercher ma structure",
        }
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
        siae_user_pending_request = self.object.siaeuserrequest_set.filter(initiator=self.request.user).pending()
        context["siae_user_pending_request"] = siae_user_pending_request
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")},
                {"title": "Rechercher ma structure", "url": reverse_lazy("dashboard_siaes:siae_search_by_siret")},
            ],
            "current": "Vérifier ma structure",
        }
        return context

    def form_valid(self, form):
        """
        - Siae with user? add the User to the Siae
        - Siae with existing user(s)? go through the invitation workflow
        """
        if not self.object.users.count():
            self.object.users.add(self.request.user)
            c = api_brevo.BrevoCompanyApiClient()
            c.link_company_with_contact_list(self.object.brevo_company_id, [self.request.user.email])
            return super().form_valid(form)
        else:
            # create SiaeUserRequest + send request email to assignee
            for assignee in self.object.users.all():
                siae_user_request = SiaeUserRequest.objects.create(
                    siae=self.object,
                    initiator=self.request.user,
                    assignee=assignee,
                    logs=[{"action": "create", "timestamp": timezone.now().isoformat()}],
                )
                send_siae_user_request_email_to_assignee(siae_user_request)
            success_message = "La demande a été envoyée aux gestionnaires de la strucure."
            messages.add_message(self.request, messages.SUCCESS, success_message)
            return HttpResponseRedirect(reverse_lazy("dashboard:home"))

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit", args=[self.kwargs.get("slug")])


class SiaeUsersView(SiaeMemberRequiredMixin, DetailView):
    template_name = "dashboard/siae_users.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()

    def get_context_data(self, **kwargs):
        """
        - check if there isn't any pending SiaeUserRequest
        """
        context = super().get_context_data(**kwargs)
        siae_user_pending_request = self.object.siaeuserrequest_set.filter(assignee=self.request.user).pending()
        context["siae_user_pending_requests"] = siae_user_pending_request
        context["breadcrumb_links"] = [{"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")}]
        context["breadcrumb_current"] = f"{self.object.name_display} : collaborateurs"
        return context


class SiaeEditActivitiesView(SiaeMemberRequiredMixin, DetailView):
    template_name = "dashboard/siae_edit_activities.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_links"] = [{"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")}]
        context["breadcrumb_current"] = f"{self.object.name_display} : modifier"

        context["grouped_activities"] = self.object.grouped_activities
        return context


class SiaeEditActivitiesDeleteView(SiaeMemberRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "dashboard/_siae_activity_delete_modal.html"
    model = SiaeActivity

    def get_object(self):
        siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return get_object_or_404(SiaeActivity, id=self.kwargs.get("activity_id"), siae=siae)

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.kwargs.get("slug")])

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre activité <strong>{self.object.sector}</strong> a été supprimée avec succès.")


class SiaeEditActivitiesCreateView(SiaeMemberRequiredMixin, TemplateView):
    """Display a page with a select displaying sector groups that
    will call dashboard_siaes:siae_activities_sector_form uppon
    change and load an htmx partial"""

    template_name = "dashboard/siae_edit_activities_create.html"

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Ajouter une activité"
        context["siae"] = self.siae
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")},
                {
                    "title": f"{self.siae.name_display} : modifier",
                    "url": reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.siae.slug]),
                },
            ],
            "current": context["page_title"],
        }
        context["sector_groups"] = SectorGroup.objects.all()

        return context


class SiaeEditActivitiesEditView(SiaeMemberRequiredMixin, TemplateView):
    """Display a page with a select displaying an already selected sector group
    that will call dashboard_siaes:siae_activities_sector_form uppon
    change and load an htmx partial"""

    template_name = "dashboard/siae_edit_activities_create.html"

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        self.sector_group_id = self.kwargs["sector_group_id"]
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Modifier une activité"
        context["siae"] = self.siae
        context["breadcrumb_data"] = {
            "root_dir": settings_context_processors.expose_settings(self.request)["HOME_PAGE_PATH"],
            "links": [
                {"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")},
                {
                    "title": f"{self.siae.name_display} : modifier",
                    "url": reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.siae.slug]),
                },
            ],
            "current": context["page_title"],
        }

        context["sector_groups"] = SectorGroup.objects.all()
        context["sector_group_id"] = self.sector_group_id
        return context


class SiaeActivitySectorFormView(SiaeMemberRequiredMixin, TemplateView):
    template_name = "dashboard/_siae_edit_activities_create_sector_form.html"

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        self.sector_group_id = self.request.GET.get("sector_group_id")
        if self.sector_group_id:
            self.siae_activities = SiaeActivity.objects.with_siae_and_sector_group(self.siae, self.sector_group_id)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["siae"] = self.siae

        # This subquery is used to find the link between a displayed sector and
        # an already existing activity
        activity_sector_subquery = SiaeActivity.objects.filter(siae=self.siae, sector=OuterRef("id")).values("id")

        if self.sector_group_id:
            context["sectors"] = Sector.objects.filter(group_id=self.sector_group_id).annotate(
                linked_activity_id=Subquery(activity_sector_subquery[:1])
            )
        else:  # when no sector group is selected from the dropdown
            context["sectors"] = None

        # Get existing sector ids and convert to string in order to be compared with html input value
        if hasattr(self, "siae_activities") and self.siae_activities:
            existing_sector_ids = [activity.sector.id for activity in self.siae_activities]
            context["existing_sector_ids"] = existing_sector_ids

        return context


class HtmxActivityValidationMixin:

    def form_invalid(self, form):
        """Form htmx, not sent in case of valid form because lost in redirect"""
        response = super().form_invalid(form)
        response.headers["formInvalid"] = "true"
        return response


class SiaeActivityCreateView(HtmxActivityValidationMixin, SiaeMemberRequiredMixin, CreateView):
    template_name = "dashboard/partial_activity_create_form.html"
    form_class = SiaeActivityForm
    model = SiaeActivity

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        # It's part of the url because it's necessary to also have it in POST
        # to set the form prefix
        self.sector_id = self.kwargs.get("sector_id")

    def get_context_data(self, **kwargs):
        """For POST url siae argument"""
        ctx = super().get_context_data(**kwargs)
        ctx["siae"] = self.siae
        ctx["sector_id"] = self.sector_id
        return ctx

    def get_success_url(self):
        """Redirect to the siae detail page"""
        return reverse_lazy("dashboard_siaes:siae_activities_edit", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        """Bind to be created activity instance to siae instance"""
        form.instance.siae = self.siae
        return super().form_valid(form)

    def get_initial(self):
        """Set sector as initial data for hidden input sector field"""
        initial = super().get_initial()
        initial["sector"] = self.sector_id
        return initial

    def get_form_kwargs(self):
        """Add a prefix to form inputs name and id to avoid conflicts with other forms in the page"""
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = f"sector-{self.sector_id}"
        return kwargs


class SiaeActivityDetailView(UserPassesTestMixin, DetailView):
    template_name = "dashboard/partial_activity_detail.html"
    model = SiaeActivity

    def test_func(self):
        """Check that only user linked to the Siae can see this activity"""
        return SiaeActivity.objects.filter(pk=self.kwargs["pk"], siae__users=self.request.user).exists()


class SiaeActivityEditView(HtmxActivityValidationMixin, UserPassesTestMixin, UpdateView):
    template_name = "dashboard/partial_activity_edit_form.html"
    form_class = SiaeActivityForm
    model = SiaeActivity

    def test_func(self):
        """Check that only user linked to the Siae can edit this activity"""
        return SiaeActivity.objects.filter(pk=self.kwargs["pk"], siae__users=self.request.user).exists()

    def get_form_kwargs(self):
        """Add a prefix to form inputs name and id to avoid conflicts with other forms in the page"""
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = f"activity-{self.object.pk}"
        return kwargs

    def get_context_data(self, **kwargs):
        """Really ugly but necessary to the even more ugly PerimetersMultiAutocomplete"""
        ctx = super().get_context_data(**kwargs)
        ctx["current_locations"] = list(self.object.locations.values("id", "slug", "name"))
        return ctx

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_activities_edit", kwargs={"pk": self.object.pk})


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
            context["label_formset"] = SiaeLabelOldFormSet(self.request.POST, instance=self.object)
        else:
            context["label_formset"] = SiaeLabelOldFormSet(instance=self.object)
        context["last_3_siae_content_filled_full_annotated"] = (
            Siae.objects.with_content_filled_stats()
            .filter(content_filled_full_annotated=True)
            .exclude(id=self.object.id)
            .order_by("-updated_at")[:3]
        )
        context["breadcrumb_links"] = [{"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")}]
        context["breadcrumb_current"] = f"{self.object.name_display} : modifier"
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        label_formset = SiaeLabelOldFormSet(request.POST, instance=self.object)
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
        return reverse_lazy("dashboard_siaes:siae_edit_info", args=[self.kwargs.get("slug")])


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
        context["breadcrumb_links"] = [{"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")}]
        context["breadcrumb_current"] = f"{self.object.name_display} : modifier"
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
        return reverse_lazy("dashboard_siaes:siae_edit_offer", args=[self.kwargs.get("slug")])


class SiaeEditContactView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditContactForm
    template_name = "dashboard/siae_edit_contact.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_contact", args=[self.kwargs.get("slug")])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_links"] = [{"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")}]
        context["breadcrumb_current"] = f"{self.object.name_display} : modifier"
        return context


class SiaeUserRequestConfirmView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeUserRequestForm
    template_name = "siaes/_siae_user_request_confirm_modal.html"
    context_object_name = "siaeuserrequest"
    queryset = SiaeUserRequest.objects.all()
    success_message = "L'utilisateur a été rattaché à votre structure."
    # success_url = reverse_lazy("dashboard_siaes:siae_users")

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
        send_siae_user_request_response_email_to_initiator(self.object)
        c = api_brevo.BrevoCompanyApiClient()
        c.link_company_with_contact_list(self.object.siae.brevo_company_id, [self.object.initiator.email])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_users", args=[self.kwargs.get("slug")])


class SiaeUserRequestCancelView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeUserRequestForm
    template_name = "siaes/_siae_user_request_cancel_modal.html"
    context_object_name = "siaeuserrequest"
    queryset = SiaeUserRequest.objects.all()
    success_message = "L'utilisateur sera informé de votre refus."
    # success_url = reverse_lazy("dashboard_siaes:siae_users")

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
        send_siae_user_request_response_email_to_initiator(self.object)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_users", args=[self.kwargs.get("slug")])


class SiaeUserDeleteView(SiaeMemberRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "siaes/_siae_user_delete_modal.html"
    model = SiaeUser
    # success_message = "L'utilisateur a été supprimé de votre structure."
    # success_url = reverse_lazy("dashboard_siaes:siae_users")

    def get_object(self):
        siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return get_object_or_404(SiaeUser, siae=siae, id=self.kwargs.get("siaeuser_id"))

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_users", args=[self.kwargs.get("slug")])

    def get_success_message(self, cleaned_data):
        return mark_safe(
            f"L'utilisateur <strong>{self.object.user.full_name}</strong> a été supprimé de votre structure avec succès."  # noqa
        )
