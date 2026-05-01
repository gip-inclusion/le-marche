import logging

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, TemplateView

from lemarche.testimonials import constants as testimonial_constants
from lemarche.testimonials.models import SiaeTestimonial
from lemarche.testimonials.tasks import send_testimonial_received_email
from lemarche.users.models import User


logger = logging.getLogger(__name__)


class TestimonialSubmitForm(forms.Form):
    content = forms.CharField(
        label="Votre témoignage",
        max_length=testimonial_constants.CONTENT_MAX_LENGTH,
        widget=forms.Textarea(attrs={"rows": 5, "maxlength": testimonial_constants.CONTENT_MAX_LENGTH}),
    )
    author_first_name = forms.CharField(label="Votre prénom", max_length=255)
    author_last_name = forms.CharField(label="Votre nom", max_length=255, required=False)
    author_organization = forms.CharField(label="Votre organisation", max_length=100, required=False)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_honeypot(self):
        value = self.cleaned_data.get("honeypot", "")
        if value:
            raise forms.ValidationError("Formulaire invalide.")
        return value


class TestimonialSubmitView(FormView):
    template_name = "testimonials/submit.html"
    form_class = TestimonialSubmitForm

    def dispatch(self, request, *args, **kwargs):
        self.testimonial = get_object_or_404(SiaeTestimonial, token=self.kwargs["token"])
        if self.testimonial.status != testimonial_constants.STATUS_SENT:
            return HttpResponseRedirect(reverse("testimonials:confirm", kwargs={"token": self.kwargs["token"]}))
        if not self.testimonial.is_token_valid:
            messages.error(request, "Ce lien a expiré. Contactez la structure pour recevoir un nouveau lien.")
            return HttpResponseRedirect(reverse("pages:home"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testimonial"] = self.testimonial
        context["content_max_length"] = testimonial_constants.CONTENT_MAX_LENGTH
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        self.testimonial.content = data["content"]
        self.testimonial.author_first_name = data["author_first_name"]
        self.testimonial.author_last_name = data.get("author_last_name", "")
        self.testimonial.author_organization = data.get("author_organization", "")
        self.testimonial.status = testimonial_constants.STATUS_SUBMITTED
        self.testimonial.submitted_at = timezone.now()

        buyer_user = User.objects.filter(email=self.testimonial.client_email).first()
        if buyer_user:
            self.testimonial.buyer_user = buyer_user
            if not self.testimonial.author_organization and buyer_user.company_name:
                self.testimonial.author_organization = buyer_user.company_name

        self.testimonial.save(
            update_fields=[
                "content",
                "author_first_name",
                "author_last_name",
                "author_organization",
                "buyer_user",
                "status",
                "submitted_at",
                "updated_at",
            ]
        )

        send_testimonial_received_email(self.testimonial)

        return HttpResponseRedirect(reverse("testimonials:confirm", kwargs={"token": self.kwargs["token"]}))


class TestimonialConfirmView(TemplateView):
    template_name = "testimonials/confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["testimonial"] = get_object_or_404(SiaeTestimonial, token=self.kwargs["token"])
        return context
