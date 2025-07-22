from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import OuterRef, Subquery
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView
from django.views.generic.edit import FormMixin

from lemarche.sectors.models import Sector, SectorGroup
from lemarche.siaes.models import Siae, SiaeActivity, SiaeUser, SiaeUserRequest
from lemarche.utils import settings_context_processors
from lemarche.utils.apis import api_brevo
from lemarche.utils.mixins import SiaeMemberRequiredMixin, SiaeUserAndNotMemberRequiredMixin, SiaeUserRequiredMixin
from lemarche.utils.s3 import S3Upload
from lemarche.www.dashboard_siaes.forms import (
    SiaeActivitiesCreateForm,
    SiaeActivityForm,
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

        siae_activities = SiaeActivity.objects.with_sector_and_sector_group(self.object)

        grouped_activities = {}

        for activity in siae_activities:
            group = activity.sector.group
            sector = activity.sector

            if group not in grouped_activities:
                grouped_activities[group] = {}

            grouped_activities[group][sector] = activity

        context["grouped_activities"] = grouped_activities
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
        return mark_safe(f"Votre activité <strong>{self.object.sector}</strong> a été supprimée avec succès.")


class SiaeEditActivitiesCreateView(SiaeMemberRequiredMixin, FormView):
    template_name = "dashboard/siae_edit_activities_create.html"
    form_class = SiaeActivitiesCreateForm

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        created_count = 0
        created_siae_activities = []
        selected_sectors = request.POST.getlist("sectors")

        for sector_id in selected_sectors:
            sector = Sector.objects.get(id=sector_id)
            presta_type = self.request.POST.getlist(f"presta_type_{sector_id}")
            geo_range = self.request.POST.get(f"geo_range_{sector_id}")
            geo_range_custom_distance = self.request.POST.get(f"geo_range_custom_distance_{sector_id}")
            locations = self.request.POST.getlist(f"locations_{sector_id}")

            form_data = {
                "siae": self.siae.id,
                "sectors": [sector],
                "presta_type": presta_type,
                "geo_range": geo_range,
                "geo_range_custom_distance": geo_range_custom_distance,
                "locations": [loc for loc in locations if loc],
            }

            form = SiaeActivityForm(data=form_data)

            if form.is_valid():
                if SiaeActivity.objects.filter(siae=self.siae, sector=sector).exists():
                    # If SiaeActivity already exists, skip it
                    continue
                siae_activity = SiaeActivity.objects.create(
                    siae=self.siae,
                    sector=sector,
                    presta_type=form.cleaned_data["presta_type"],
                    geo_range=form.cleaned_data["geo_range"],
                    geo_range_custom_distance=form.cleaned_data["geo_range_custom_distance"],
                )
                siae_activity.locations.set(form.cleaned_data["locations"])
                created_count += 1
                created_siae_activities.append(sector.name)
            else:
                return self.form_invalid(form)

        # If no sector is selected or no new activity is created, show an error message
        if not selected_sectors or created_count == 0:
            form = self.get_form()
            form.add_error(None, "Veuillez sélectionner au moins une nouvelle activité.")
            return self.form_invalid(form)

        messages.success(
            self.request,
            self.get_success_message(created_siae_activities, created_count),
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
        context["sector_groups"] = SectorGroup.objects.all()

        return context

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.kwargs.get("slug")])

    def get_success_message(self, created_siae_activities, created_count):
        if created_count == 1:
            return mark_safe(f"Votre activité <strong>{created_siae_activities[0]}</strong> a été créée avec succès.")
        else:
            sectors = ", ".join([sector for sector in created_siae_activities])
            return mark_safe(f"Les activités suivantes ont été créées avec succès : <strong>{sectors}</strong>.")


class SiaeEditActivitiesEditView(SiaeMemberRequiredMixin, SuccessMessageMixin, FormView):
    template_name = "dashboard/siae_edit_activities_create.html"
    form_class = SiaeActivitiesCreateForm
    success_message = "Votre activité a été modifiée avec succès."

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        self.sector_group_id = self.kwargs["sector_group_id"]
        self.siae_activities = SiaeActivity.objects.with_siae_and_sector_group(self.siae, self.sector_group_id)
        self.locations = self.siae_activities.get_related_locations()

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        self.sector_group_id = self.kwargs["sector_group_id"]
        self.siae_activities = SiaeActivity.objects.with_siae_and_sector_group(self.siae, self.sector_group_id)
        self.locations = self.siae_activities.get_related_locations()

        updated_count = 0
        updated_siae_activities = []
        selected_sectors = request.POST.getlist("sectors")

        # Create a dictionary to easily access activities by sector ID
        activities_by_sector = {str(activity.sector.id): activity for activity in self.siae_activities}

        for sector_id in selected_sectors:
            # Check if SiaeActivity already exists for this sector
            if sector_id in activities_by_sector:
                activity = activities_by_sector[sector_id]
                sector = activity.sector

                presta_type = self.request.POST.getlist(f"presta_type_{sector_id}")
                geo_range = self.request.POST.get(f"geo_range_{sector_id}")
                geo_range_custom_distance = self.request.POST.get(f"geo_range_custom_distance_{sector_id}")
                locations = self.request.POST.getlist(f"locations_{sector_id}")

                form_data = {
                    "siae": self.siae.id,
                    "sectors": [sector.id],
                    "presta_type": presta_type,
                    "geo_range": geo_range,
                    "geo_range_custom_distance": geo_range_custom_distance,
                    "locations": [loc for loc in locations if loc],
                }

                form = SiaeActivityForm(data=form_data, instance=activity)

                if form.is_valid():
                    activity.presta_type = form.cleaned_data["presta_type"]
                    activity.geo_range = form.cleaned_data["geo_range"]
                    activity.geo_range_custom_distance = form.cleaned_data["geo_range_custom_distance"]
                    activity.save()

                    activity.locations.set(form.cleaned_data["locations"])

                    updated_count += 1
                    updated_siae_activities.append(sector.name)
                else:
                    return self.form_invalid(form)

        messages.success(
            self.request,
            self.get_success_message(updated_siae_activities, updated_count),
        )

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Modifier une activité"
        context["siae"] = self.siae
        context["current_locations"] = list(self.locations.values("id", "slug", "name"))
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
        context["sector_group_id"] = self.kwargs.get("sector_group_id")
        return context

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_edit_activities", args=[self.kwargs.get("slug")])

    def get_success_message(self, updated_siae_activities, updated_count):
        if updated_count == 1:
            return mark_safe(
                f"Votre activité <strong>{updated_siae_activities[0]}</strong> a été modifiée avec succès."
            )
        else:
            sectors = ", ".join([sector for sector in updated_siae_activities])
            return mark_safe(f"Les activités suivantes ont été modifiées avec succès : <strong>{sectors}</strong>.")


class SiaeActivitySectorFormView(TemplateView):
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
        context["sectors"] = Sector.objects.filter(group_id=self.sector_group_id).annotate(
            linked_activity_id=Subquery(activity_sector_subquery[:1])
        )

        # Get existing sector ids and convert to string in order to be compared with html input value
        if hasattr(self, "siae_activities") and self.siae_activities:
            existing_sector_ids = [str(activity.sector.id) for activity in self.siae_activities]
            context["existing_sector_ids"] = existing_sector_ids

        return context


class SiaeActivityPrestaGeoFormView(FormView):
    template_name = "dashboard/_siae_edit_activities_create_presta_geo_form.html"
    form_class = SiaeActivityForm

    def get(self, request, *args, **kwargs):
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sector_id = self.request.GET.get("sectors")
        if sector_id:
            context["sector_id"] = sector_id

            # Get existing activity data
            try:
                existing_activity = SiaeActivity.objects.get(siae=self.siae, sector_id=sector_id)
                context["existing_presta_types"] = existing_activity.presta_type
                context["existing_geo_range"] = existing_activity.geo_range
                context["existing_geo_range_custom_distance"] = existing_activity.geo_range_custom_distance

                if hasattr(existing_activity, "locations"):
                    context["existing_locations"] = existing_activity.locations.all()
            except SiaeActivity.DoesNotExist:
                pass
        return context


class SiaeActivityCreateView(CreateView):
    template_name = "dashboard/partial_activity_create_form.html"  # fixme inherit form
    form_class = SiaeActivityForm
    model = SiaeActivity

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.siae = Siae.objects.get(slug=self.kwargs.get("slug"))
        self.sector = self.request.GET.get("selected_sector")

    def get_context_data(self, **kwargs):
        """For POST url siae argument"""
        ctx = super().get_context_data(**kwargs)
        ctx["siae"] = self.siae
        return ctx

    def get_success_url(self):
        """Redirect to the siae detail page"""
        return reverse_lazy("dashboard_siaes:siae_activities_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        """Bind to be created activity instance to siae instance"""
        form.instance.siae = self.siae
        return super().form_valid(form)

    def get_initial(self):
        """Set sector as initial data for hidden input sector field"""
        initial = super().get_initial()
        initial["sector"] = self.sector
        return initial


class SiaeActivityDetailView(DetailView):
    template_name = "dashboard/partial_activity_detail.html"
    model = SiaeActivity


class SiaeActivityEditView(UpdateView):
    template_name = "dashboard/partial_activity_edit_form.html"
    form_class = SiaeActivityForm
    model = SiaeActivity

    def get_form_kwargs(self):
        """Add a prefix to form inputs name and id to avoid conflicts with other forms in the page"""
        kwargs = super().get_form_kwargs()
        kwargs["prefix"] = f"activity-{self.object.pk}"
        return kwargs

    def get_success_url(self):
        return reverse_lazy("dashboard_siaes:siae_activities_detail", kwargs={"pk": self.object.pk})


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
