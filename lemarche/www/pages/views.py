import logging
from django.shortcuts import render

logger = logging.getLogger(__name__)


def inclusion(request, template_name="frontend/pages/inclusion.html"):
    context = {}
    return render(request, template_name, context)
