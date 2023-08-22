from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormMixin

from lemarche.networks.models import Network
from lemarche.siaes.models import Siae
from lemarche.tenders.models import Tender, TenderSiae
from lemarche.utils.mixins import NetworkMemberRequiredMixin
from lemarche.www.siaes.forms import NetworkSiaeFilterForm


class DashboardNetworkDetailView(NetworkMemberRequiredMixin, DetailView):
    template_name = "networks/dashboard_network_detail.html"
    queryset = Network.objects.prefetch_related("siaes").all()
    context_object_name = "network"


class DashboardNetworkSiaeListView(NetworkMemberRequiredMixin, FormMixin, ListView):
    template_name = "networks/dashboard_network_siae_list.html"
    form_class = NetworkSiaeFilterForm
    queryset = Siae.objects.prefetch_related("networks").all()
    context_object_name = "siaes"

    def get_queryset(self):
        qs = super().get_queryset()
        # first get the network's siaes
        self.network = Network.objects.get(slug=self.kwargs.get("slug"))
        qs = qs.filter(networks__in=[self.network]).with_tender_stats().annotate_with_brand_or_name(with_order_by=True)
        # then filter with the form
        self.filter_form = NetworkSiaeFilterForm(data=self.request.GET)
        qs = self.filter_form.filter_queryset(qs)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        siae_search_form = self.filter_form if self.filter_form else NetworkSiaeFilterForm(data=self.request.GET)
        context["form"] = siae_search_form
        return context


class DashboardNetworkSiaeTenderListView(NetworkMemberRequiredMixin, ListView):
    template_name = "networks/dashboard_network_siae_tender_list.html"
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
                    return redirect("dashboard_networks:siae_list", slug=self.network.slug)
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


class DashboardNetworkTenderListView(NetworkMemberRequiredMixin, ListView):
    template_name = "networks/dashboard_network_tender_list.html"
    queryset = Tender.objects.all()
    context_object_name = "tenders"
    paginate_by = 10
    paginator_class = Paginator

    def get(self, request, *args, **kwargs):
        # self.network = self.get_object()
        self.network = Network.objects.prefetch_related("siaes").get(slug=self.kwargs.get("slug"))
        self.network_siaes = self.network.siaes.all()
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.prefetch_many_to_many().select_foreign_keys()
        qs = qs.filter_with_siaes(self.network_siaes)
        qs = qs.with_network_siae_stats(self.network_siaes)
        qs = qs.order_by_deadline_date()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        return context


class DashboardNetworkTenderDetailView(NetworkMemberRequiredMixin, DetailView):
    model = Tender
    template_name = "networks/dashboard_network_tender_detail.html"
    context_object_name = "tender"

    def get_object(self):
        self.network = Network.objects.prefetch_related("siaes").get(slug=self.kwargs.get("slug"))
        self.network_siaes = self.network.siaes.all()
        self.tender = get_object_or_404(
            Tender.objects.validated().with_network_siae_stats(self.network_siaes),
            slug=self.kwargs.get("tender_slug"),
        )
        return self.tender

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["network"] = self.network
        return context


class DashboardNetworkTenderSiaeListView(NetworkMemberRequiredMixin, ListView):
    template_name = "networks/dashboard_network_tender_siae_list.html"
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
