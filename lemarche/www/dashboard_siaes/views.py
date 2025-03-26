from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.siaes.models import Siae, SiaeActivity, SiaeUser, SiaeUserRequest
from lemarche.utils import settings_context_processors
from lemarche.utils.apis import api_brevo
from lemarche.utils.mixins import SiaeMemberRequiredMixin, SiaeUserAndNotMemberRequiredMixin, SiaeUserRequiredMixin
from lemarche.utils.s3 import S3Upload
from lemarche.www.dashboard_siaes.forms import (
    SiaeActivitiesCreateForm,
    SiaeClientReferenceFormSet,
    SiaeEditContactForm,
    SiaeEditInfoForm,
    SiaeEditLinksForm,
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
        siae_user_pending_request = self.object.siaeuserrequest_set.initiator(self.request.user).pending()
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
            api_brevo.link_company_with_contact_list(self.object)
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
        siae_user_pending_request = self.object.siaeuserrequest_set.assignee(self.request.user).pending()
        context["siae_user_pending_request"] = siae_user_pending_request
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
        return context


class SiaeEditActivitiesDeleteView(SiaeMemberRequiredMixin, SuccessMessageMixin, DeleteView):
    template_name = "dashboard/_siae_activity_delete_modal.html"
    model = SiaeActivity
    # success_url = reverse_lazy("dashboard_siaes:siae_edit_activities")
    # success_message = "Votre activité a été supprimée avec succès."

    def get_object(self):
        siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return get_object_or_404(SiaeActivity, id=self.kwargs.get("activity_id"), siae=siae)

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.kwargs.get("slug")])

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre activité <strong>{self.object.sector_group}</strong> a été supprimée avec succès.")


class SiaeEditActivitiesCreateView(SiaeMemberRequiredMixin, CreateView):
    template_name = "dashboard/siae_edit_activities_create.html"
    form_class = SiaeActivitiesCreateForm
    # success_url = reverse_lazy("dashboard_siaes:siae_edit_activities")
    # success_message = "Votre activité a été crée avec succès."

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        siae_activity = form.save(commit=False)
        siae_activity.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        siae_activity.save()
        form.save_m2m()

        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data),
        )
        return HttpResponseRedirect(self.get_success_url())

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
        return context

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.kwargs.get("slug")])

    def get_success_message(self, cleaned_data):
        return mark_safe(f"Votre activité <strong>{cleaned_data['sector_group']}</strong> a été créée avec succès.")


class SiaeEditActivitiesEditView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "dashboard/siae_edit_activities_create.html"
    form_class = SiaeActivitiesCreateForm
    # success_url = reverse_lazy("dashboard_favorites:list_detail")
    success_message = "Votre activité a été modifiée avec succès."

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().post(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(SiaeActivity, siae__slug=self.kwargs.get("slug"), id=self.kwargs.get("activity_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Modifier une activité"
        context["siae"] = self.siae
        context["activity"] = self.object
        context["current_locations"] = list(self.object.locations.values("id", "slug", "name"))
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
        return context

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.kwargs.get("slug")])


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


class SiaeEditLinksView(SiaeMemberRequiredMixin, SuccessMessageMixin, UpdateView):
    form_class = SiaeEditLinksForm
    template_name = "dashboard/siae_edit_links.html"
    context_object_name = "siae"
    queryset = Siae.objects.all()
    success_message = "Vos modifications ont bien été prises en compte."

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_links", args=[self.kwargs.get("slug")])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["breadcrumb_links"] = [{"title": settings.DASHBOARD_TITLE, "url": reverse_lazy("dashboard:home")}]
        context["breadcrumb_current"] = f"{self.object.name_display} : modifier"
        return context


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
        api_brevo.link_company_with_contact_list(self.object.siae)
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
