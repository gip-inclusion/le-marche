from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.views.generic import CreateView, DetailView, ListView

from lemarche.tenders.models import Tender
from lemarche.users.models import User
from lemarche.www.tenders.forms import AddTenderForm
from lemarche.www.tenders.tasks import find_opportunities_for_siaes


TITLE_DETAIL_PAGE_SIAE = "Trouver de nouvelles opportunités"
TITLE_DETAIL_PAGE_OTHERS = "Besoins en cours"


class TenderCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "tenders/create.html"
    form_class = AddTenderForm
    context_object_name = "tender"
    success_message = """
        Votre besoin <strong>{}</strong> est déposé sur le marché et les structures
        correspondants à vos critères seront notifiés
    """
    success_url = reverse_lazy("tenders:list")

    def form_valid(self, form):
        tender = form.save(commit=False)
        tender.author = self.request.user
        tender.save()
        form.save_m2m()
        messages.add_message(
            self.request,
            messages.SUCCESS,
            self.get_success_message(form.cleaned_data, tender),
        )
        # task
        find_opportunities_for_siaes(tender)
        return HttpResponseRedirect(self.success_url)

    def get(self, request, *args, **kwargs):
        # siaes cannot add tenders
        if request.user.kind == User.KIND_SIAE:
            return redirect("tenders:list")
        else:
            return super().get(request, *args, **kwargs)

    def get_initial(self):
        user = self.request.user
        return {
            "contact_first_name": user.first_name,
            "contact_last_name": user.last_name,
            "contact_email": user.email,
            "contact_phone": user.phone,
        }

    def get_success_message(self, cleaned_data, tender):
        return mark_safe(self.success_message.format(tender.title))


class TenderListView(LoginRequiredMixin, ListView):
    template_name = "tenders/list.html"
    model = Tender
    context_object_name = "tenders"
    paginate_by = 10
    paginator_class = Paginator

    def get_queryset(self):
        user = self.request.user
        queryset = Tender.objects.none()
        if user.kind == User.KIND_SIAE and user.siaes:
            # TODO: manage many siaes
            siae = user.siaes.first()
            if siae:
                queryset = Tender.objects.filter_with_siae(siae)
        else:
            queryset = Tender.objects.by_user(user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_kind = self.request.user.kind if self.request.user.is_authenticated else "anonymous"
        context["page_title"] = TITLE_DETAIL_PAGE_SIAE if user_kind == User.KIND_SIAE else TITLE_DETAIL_PAGE_OTHERS
        return context


class TenderDetail(LoginRequiredMixin, DetailView):
    model = Tender
    template_name = "tenders/detail.html"
    context_object_name = "tender"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_kind = self.request.user.kind if self.request.user.is_authenticated else "anonymous"
        context["parent_title"] = TITLE_DETAIL_PAGE_SIAE if user_kind == User.KIND_SIAE else TITLE_DETAIL_PAGE_OTHERS
        return context
