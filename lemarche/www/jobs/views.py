from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from lemarche.jobs.models import Appellation
from lemarche.sectors.models import Sector
from lemarche.www.jobs.forms import SectorAppellationsForm


class SectorAppellationsFormView(TemplateView):
    """
    Form page to show how appellations are dynamically displayed based on selected sectors.
    """

    template_name = "jobs/sector_appellations_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SectorAppellationsForm()
        return context


class SectorAppellationsView(View):
    """
    HTMX endpoint to get appellations for given sector(s).
    Returns HTML partial with appellations list.
    Accepts one or multiple sector slugs as query parameter.
    """

    template_name = "jobs/partial_sector_appellations.html"

    def get(self, request, *args, **kwargs):
        # getlist allows multiple ?sectors=slug1&sectors=slug2
        sectors_params = request.GET.getlist("sectors")
        if not sectors_params:
            return HttpResponse("", status=200)

        # to avoid DoS
        if len(sectors_params) > 10:
            return HttpResponse("", status=400)

        sectors = Sector.objects.filter(slug__in=sectors_params)
        appellations = Appellation.objects.filter(sectors__in=sectors).distinct().order_by("name")

        return render(
            request,
            self.template_name,
            {
                "appellations": appellations,
            },
        )
